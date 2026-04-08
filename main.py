from scraper import WebScrapper
from rag import Rag_Handler
from model import ModelHandler, config_for_rag_coder
from database import SQDB
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',filename='my_app.log',filemode='a',)
logger = logging.getLogger(__name__)

class Orchestrator:
    """High-level orchestrator that ties scraping, storage, and RAG prep.

    The `Orchestrator` coordinates fetching page content via `WebScrapper`,
    storing content in the `SQDB` database, and preparing documents for
    retrieval-augmented generation (RAG) using `Rag_Handler`.
    """
    
    def __init__(self,query,name):
        """Create an Orchestrator instance.

        This initializer currently performs no special setup, but it exists
        to allow future extension (dependency injection, configuration, etc.).
        """
        self.query = query
        self.name = name
        
        self.model_handler = ModelHandler()
        self.rag_handler = Rag_Handler(ollama_ef=self.model_handler.get_ollama_ef())
        self.db = SQDB("web_content.db")
        self.scrapper = WebScrapper("https://docs.trychroma.com/docs/overview/introduction")


    def scrape_and_store(self, url, name):
        """Scrape a URL and store its content in the SQLite database.

        If the URL already exists in the database, it will not be added again.

        Args:
            url (str): The target URL to scrape (expected in the format used
                       by `WebScrapper.get_data`).
            name (str): The name of the main page.
        """
        try:
            self.db.create_table()
            try:
                content = self.scrapper.get_data()
            except Exception:
                logger.exception("Failed to fetch main URL %s", url)
                return

            start_url = self.scrapper.get_start_url()
            if not self.db.if_exists_main(start_url):
                try:
                    self.db.insert_main_page(start_url, name, content)
                    logger.info("Content from %s stored in database.", url)
                except Exception:
                    logger.exception("Failed to insert main page for %s", start_url)

                links = self.scrapper.get_links(content)
                for link in links:
                    try:
                        if self.scrapper.is_url_doc(link) and not self.db.if_exists_additional(link):
                            additional_content = WebScrapper(link).get_data()
                            self.db.insert_additional_page(link, start_url, additional_content)
                            logger.info("Additional content from %s stored in database.", link)
                    except Exception:
                        logger.exception("Failed processing additional link %s", link)
            else:
                logger.info("URL %s already exists in the database. Skipping storage.", url)
        except Exception:
            logger.exception("Unexpected error during scrape_and_store for %s", url)


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
        
        for content in contents:
            try:
                chunks = self.rag_handler.chunking(content[0], 1000, 200)
                self.rag_handler.add_document(chunks)
            except Exception:
                logger.exception("Failed to chunk/add document")
        
        try:
            if contents: 
                results = self.rag_handler.query(self.query)
                logger.info("Query results for '%s': %s", self.query, results)
        except Exception:
            logger.exception("Failed to query RAG database.")
            
        logger.info("RAG preparation completed.")
        return results
    def run(self):
        """Placeholder run loop for orchestrator.

        Implement application-specific orchestration or CLI entrypoints
        here in future iterations.
        """
        try:
            response = "Error: Orchestrator failed to complete the run."
            #self.scrape_and_store("https://docs.trychroma.com/docs/overview/introduction", "introduction")
            contents = self.prepare_rag()
            results  = self.chunking(contents)
            response = self.model_handler.ask_for_code(f'query: {self.query}\n\nfindings in the library:: {results}', config_for_rag_coder)
            self.db.close()
        except Exception:
            logger.exception("Orchestrator run failed")
        print(response)
        return response

if __name__ == "__main__":
    orchestrator = Orchestrator("How to use ChromaDB with Python?", "introduction")
    orchestrator.run()
