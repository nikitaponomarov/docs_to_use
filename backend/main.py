from backend.scraper import WebScrapper
from backend.rag import Rag_Handler, get_embedding_function
from backend.model import ModelHandler, config_for_rag_coder, config_for_deprecated_checker
from backend.database import SQDB
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='my_app.log',
    filemode='a',
)
logger = logging.getLogger(__name__)

DEFAULT_EMBED_MODEL = "mxbai-embed-large"
DEFAULT_EMBED_URL = "http://localhost:11434/api/embeddings"
DEFAULT_AI_PROVIDER = "gemini"
DEFAULT_AI_MODEL = "gemini-2.5-flash"
DEFAULT_AI_BASE_URL = "http://localhost:11434"


class Orchestrator:
    """Central coordinator that connects scraping, storage, RAG, and AI inference.

    The typical lifecycle for a new library:
      1. scrape_and_learn() — fetches docs, stores raw text in SQLite, embeds into ChromaDB
      2. ask() / check_deprecated() — retrieves relevant chunks and sends them to the AI

    SQLite acts as the persistent source of truth for raw content;
    ChromaDB holds the vector index derived from it.
    """

    def __init__(self):
        self.model_handler = ModelHandler()
        self.db = SQDB("web_content.db")
        self.db.create_table()

    def has_context(self, name: str) -> bool:
        # Readiness is tracked in the COLLECTIONS table, not ChromaDB,
        # so the check survives a ChromaDB wipe/rebuild.
        return self.db.if_exists_collection(name)

    def scrape_and_learn(
        self,
        url: str,
        name: str,
        embed_model: str = DEFAULT_EMBED_MODEL,
        embed_url: str = DEFAULT_EMBED_URL,
    ):
        logger.info("Starting to learn library %s from URL %s", name, url)
        scrapper = WebScrapper(url)

        # Phase 1: fetch the landing/index page and extract sub-page links from it.
        main_content, start_url = self._process_main_page(scrapper, name, url)

        # Phase 2: crawl sub-pages found on the index, staying within the same domain.
        if main_content:
            links = scrapper.get_links(main_content)
            self._process_additional_page(scrapper, links, start_url)

        self._embed_into_chroma(name, embed_model, embed_url)
        logger.info("Learning for %s completed successfully!", name)

    def _process_main_page(self, scrapper: WebScrapper, name: str, original_url: str) -> tuple[str | None, str]:
        start_url = scrapper.get_start_url()
        if start_url and scrapper.is_url_doc(start_url):
            if self.db.if_exists_main(original_url):
                logger.info("Main page already exists in database: %s", original_url)
                return None, start_url
            try:
                content = scrapper.get_data()
                self.db.insert_main_page(original_url, name, content)
                logger.info("Inserted main page into database: %s", original_url)
                return content, start_url
            except Exception:
                logger.exception("Failed to process main page: %s", original_url)
                return None, start_url
        else:
            logger.info("URL does not appear to be a documentation page, skipping: %s", original_url)
            return None, start_url or ""

    def _process_additional_page(self, scrapper: WebScrapper, links: list[str], start_url: str):
        for link in links:
            # Only follow links that stay within the same docs domain.
            if link.startswith(start_url):
                if self.db.if_exists_additional(link):
                    logger.info("Additional page already exists in database: %s", link)
                    continue
                try:
                    content = scrapper.get_data(link)
                    self.db.insert_additional_page(link, start_url, content)
                    logger.info("Inserted additional page into database: %s", link)
                except Exception:
                    logger.exception("Failed to process additional page: %s", link)

    def _embed_into_chroma(self, name: str, embed_model: str, embed_url: str):
        # ChromaDB collection names must be lowercase with underscores only.
        safe_name = name.lower().replace(" ", "_").replace("-", "_")
        collection_name = f"{safe_name}_collection"
        self.db.insert_collection(name, collection_name, embed_model, embed_url)

        ollama_ef = get_embedding_function(model_name=embed_model, url=embed_url)
        rag_handler = Rag_Handler(ollama_ef=ollama_ef, collection_name=collection_name)

        try:
            contents = self.db.get_for_chunks(name)
        except Exception:
            logger.exception("Failed to read contents for chunking")
            return

        # Skip re-embedding if the collection already has data — idempotent by design.
        collection_size = rag_handler.collection.count()
        if collection_size == 0:
            logger.info("Collection is empty — embedding %d document(s).", len(contents))
            for content in contents:
                try:
                    chunks = rag_handler.chunking(content[0], 1000, 400)
                    rag_handler.add_document(chunks)
                except Exception:
                    logger.exception("Failed to chunk/add document")
        else:
            logger.info("Collection already has %d chunks — skipping embedding.", collection_size)

    def ask(
        self,
        query: str,
        name: str,
        ai_provider: str = DEFAULT_AI_PROVIDER,
        ai_model: str = DEFAULT_AI_MODEL,
        ai_base_url: str = DEFAULT_AI_BASE_URL,
    ) -> str:
        collection_name = self.db.get_collection_name(name)
        if not collection_name:
            return f"Error: I haven't learned about the library '{name}'."

        embed_model, embed_url = self.db.get_embed_config(name)
        ollama_ef = get_embedding_function(
            model_name=embed_model or DEFAULT_EMBED_MODEL,
            url=embed_url or DEFAULT_EMBED_URL,
        )

        rag_handler = Rag_Handler(ollama_ef=ollama_ef, collection_name=collection_name)
        results = []
        try:
            if rag_handler.collection.count() > 0:
                results = rag_handler.query(query)
                logger.info("Query results for '%s' found.", query)
            else:
                logger.warning("ChromaDB is empty for %s", name)
        except Exception:
            logger.exception("Failed to query RAG database.")

        prompt = f'query: {query}\n\nfindings in the library:: {results}'
        return self.model_handler.ask_for_code(
            prompt,
            config_for_rag_coder,
            provider=ai_provider,
            model=ai_model,
            base_url=ai_base_url,
        )

    def check_deprecated(
        self,
        code: str,
        name: str,
        rewrite: bool = True,
        ai_provider: str = DEFAULT_AI_PROVIDER,
        ai_model: str = DEFAULT_AI_MODEL,
        ai_base_url: str = DEFAULT_AI_BASE_URL,
    ) -> str:
        collection_name = self.db.get_collection_name(name)
        if not collection_name:
            return f"Error: I haven't learned about the library '{name}'."

        embed_model, embed_url = self.db.get_embed_config(name)
        ollama_ef = get_embedding_function(
            model_name=embed_model or DEFAULT_EMBED_MODEL,
            url=embed_url or DEFAULT_EMBED_URL,
        )

        rag_handler = Rag_Handler(ollama_ef=ollama_ef, collection_name=collection_name)
        results = []
        # Bias the semantic search toward deprecation/migration sections of the docs.
        deprecation_query = f"deprecated removed changed migration upgrade {code[:300]}"
        try:
            if rag_handler.collection.count() > 0:
                results = rag_handler.query(deprecation_query)
                logger.info("Deprecation query results found for code snippet.")
            else:
                logger.warning("ChromaDB is empty for %s", name)
        except Exception:
            logger.exception("Failed to query RAG database for deprecation check.")

        action = "rewrite the code using the current API" if rewrite else "identify all deprecated usages without rewriting"
        prompt = f'user code:\n```\n{code}\n```\n\ntask: {action}\n\nrelevant library documentation:\n{results}'
        return self.model_handler.ask_for_code(
            prompt,
            config_for_deprecated_checker,
            provider=ai_provider,
            model=ai_model,
            base_url=ai_base_url,
        )

    def prepare_rag(self, name: str):
        """Load stored content from the database ready for chunking."""
        try:
            contents = self.db.get_for_chunks(name)
        except Exception:
            logger.exception("Failed to read contents for chunking")
            contents = []
        return contents

    def chunking(self, contents, rag_handler: Rag_Handler, query: str):
        results = []

        collection_size = rag_handler.collection.count()
        if collection_size == 0:
            logger.info("Collection is empty — embedding %d document(s).", len(contents))
            for content in contents:
                try:
                    chunks = rag_handler.chunking(content[0], 1000, 400)
                    rag_handler.add_document(chunks)
                except Exception:
                    logger.exception("Failed to chunk/add document")
        else:
            logger.info("Collection already has %d chunks — skipping embedding.", collection_size)

        try:
            if rag_handler.collection.count() > 0:
                results = rag_handler.query(query)
                logger.info("Query results for '%s': %s", query, results)
        except Exception:
            logger.exception("Failed to query RAG database.")

        logger.info("RAG preparation completed.")
        return results


if __name__ == "__main__":
    orchestrator = Orchestrator()

    test_lib_name = "chroma_docs"
    test_url = "https://docs.trychroma.com"
    test_query = "How to use chromadb in python?"

    if not orchestrator.has_context(test_lib_name):
        print(f"Starting to learn {test_lib_name}...")
        orchestrator.scrape_and_learn(test_url, test_lib_name)
    else:
        print(f"Library {test_lib_name} already exists in the database.")

    print(f"Asking question: {test_query}")
    answer = orchestrator.ask(test_query, test_lib_name)
    print("\n--- RESPONSE ---")
    print(answer)
