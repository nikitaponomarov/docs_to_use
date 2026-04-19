from scraper import WebScrapper
from rag import Rag_Handler
from model import ModelHandler, config_for_rag_coder
from database import SQDB
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',filename='my_app.log',filemode='a',)
logger = logging.getLogger(__name__)

# Maps context_name (from frontend) → ChromaDB collection name
COLLECTION_MAP = {
    "chroma_docs":     "chroma_docs_collection",
    "gemini_api_docs": "local_docs_collection",
}

class Orchestrator:
    """High-level orchestrator that ties scraping, storage, and RAG prep.

    The `Orchestrator` coordinates fetching page content via `WebScrapper`,
    storing content in the `SQDB` database, and preparing documents for
    retrieval-augmented generation (RAG) using `Rag_Handler`.
    """
    
    def __init__(self):
        """Create an Orchestrator instance.

        This initializer currently performs no special setup, but it exists
        to allow future extension (dependency injection, configuration, etc.).
        """
        self.model_handler = ModelHandler()
        self.ollama_ef = self.model_handler.get_ollama_ef()

        self.db = SQDB("web_content.db")
        self.db.create_table()


    def has_context(self,name):
        """Check if the database already has content for the given context name.

        This method queries the `SQDB` database to determine if there is
        existing content associated with the provided context name. It returns
        a boolean indicating whether relevant content is present.

        Args:
            name (str): The context name to check for in the database.
        Returns:
            bool: True if content exists for the context name, False otherwise.
        """
        return self.db.if_exists_main(name)
    
    def scrape_and_learn(self, url: str, name: str):
        """The main method to orchestrate scraping, storing, and preparing RAG."""
        logger.info(f"Starting to learn library {name} from URL {url}")
        
        scrapper = WebScrapper(url)
        

        main_content, start_url = self._process_main_page(scrapper, name, url)
        

        if main_content:
            links = scrapper.get_links(main_content)
            self._process_additional_pages(links, start_url)
        
        self._embed_into_chroma(name)
        logger.info(f"Learning for {name} completed successfully!")

    def _process_main_page(self,scrapper: WebScrapper, name,original_url: str) -> tuple[str | None, str]:
        """Process and store the main page content in the database.

        This method takes the URL, name, and content of a main page, and
        inserts it into the `Main_Pages` table of the `SQDB` database.
        """
        start_url = scrapper.get_start_url()
        if start_url and scrapper.is_url_doc(start_url):
            if self.db.if_exists_main(original_url):
                logger.info("Main page already exists in database: %s", original_url)
                return None, start_url
            else:
                try:
                    content = scrapper.get_data()
                    self.db.insert_main_page(original_url, name, content)
                    logger.info("Inserted main page into database: %s", original_url)
                    return content, start_url
                except Exception:
                    logger.exception("Failed to process main page: %s", original_url)
        else:
            logger.info("URL does not appear to be a documentation page, skipping: %s", original_url)

    def _process_aditioonal_page(self, scrapper: WebScrapper, links:list[str], start_url:str):
        for link in links:
            if link.startswith(start_url):
                if self.db.if_exists_additional(link):
                    logger.info("Additional page already exists in database: %s", link)
                    continue
                else:
                    try:
                        content = scrapper.get_data(link)
                        self.db.insert_additional_page(link, start_url, content)
                        logger.info("Inserted additional page into database: %s", link)
                    except Exception:
                        logger.exception("Failed to process additional page: %s", link)
    def _embed_into_chroma(self, name):
        """Initialize the Chroma collection for RAG embedding.

        This method creates a persistent Chroma client and retrieves or creates
        a collection with the specified name. The collection is configured to
        use the `ollama_ef` embedding function provided by the model handler.

        Args:
            collection_name (str): The name of the Chroma collection to create or retrieve.
        """
        safe_name = name.lower().replace(" ", "_").replace("-", "_")
        collection_name = f"{safe_name}_collection"
        self.db.insert_collection(name, collection_name)
        """Initialize the Chroma collection for RAG embedding."""
        rag_handler = Rag_Handler(ollama_ef=self.ollama_ef, collection_name=collection_name)
        try:
            contents = self.db.get_for_chunks(name)
        except Exception:
            logger.exception("Failed to read contents for chunking")
            return

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
    def ask(self, query: str, name: str) -> str:
            
        collection_name = self.db.get_collection_name(name)
        
        if not collection_name:
            return f"Error: I haven't learned about the library '{name}'."

        rag_handler = Rag_Handler(ollama_ef=self.ollama_ef, collection_name=collection_name)
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
        response = self.model_handler.ask_for_code(prompt, config_for_rag_coder)
        
        return response

    def prepare_rag(self):
        """Load stored content, chunk it, and add chunks to the RAG collection.

        This method reads all available content from the database, splits
        each document into chunks using `Rag_Handler.chunking`, and adds the
        resulting chunks to the collection via `Rag_Handler.add_document`.
        """

        try:
            contents = self.db.get_for_chunks(self.name)
        except Exception:
            logger.exception("Failed to read contents for chunking")
            contents = []
        return contents
    def chunking(self, contents):
        results = []

        collection_size = self.rag_handler.collection.count()

        if collection_size == 0:
            logger.info("Collection is empty — embedding %d document(s).", len(contents))
            for content in contents:
                try:
                    chunks = self.rag_handler.chunking(content[0], 1000, 400)
                    self.rag_handler.add_document(chunks)
                except Exception:
                    logger.exception("Failed to chunk/add document")
        else:
            logger.info("Collection already has %d chunks — skipping embedding.", collection_size)

        try:
            if self.rag_handler.collection.count() > 0:
                results = self.rag_handler.query(self.query)
                logger.info("Query results for '%s': %s", self.query, results)
        except Exception:
            logger.exception("Failed to query RAG database.")

        logger.info("RAG preparation completed.")
        return results

if __name__ == "__main__":
    if __name__ == "__main__":
        orchestrator = Orchestrator()
        
        test_lib_name = "chroma_docs"
        test_url = "https://docs.trychroma.com"
        test_query = "How to use chromadb in python?"

        #Check if we already have content for this library`
        if not orchestrator.has_context(test_lib_name):
            print(f"Starting to learn {test_lib_name}...")
            orchestrator.scrape_and_learn(test_url, test_lib_name)
        else:
            print(f"Library {test_lib_name} already exists in the database.")
        # 
        print(f"Asking question: {test_query}")
        answer = orchestrator.ask(test_query, test_lib_name)
        print("\n--- GEMINI RESPONSE ---")
        print(answer)
