from scraper import WebScrapper
from rag import Rag_Handler
from database import SQDB
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        pass

    def scrape_and_store(self, url, name):
        """Scrape a URL and store its content in the SQLite database.

        If the URL already exists in the database, it will not be added again.

        Args:
            url (str): The target URL to scrape (expected in the format used
                       by `WebScrapper.get_data`).
            name (str): The name of the main page.
        """
        scrapper = WebScrapper(url)
        db = SQDB("web_content.db")
        try:
            db.create_table()
            try:
                content = scrapper.get_data()
            except Exception:
                logger.exception("Failed to fetch main URL %s", url)
                return

            start_url = scrapper.get_start_url()
            if not db.if_exists_main(start_url):
                try:
                    db.insert_main_page(start_url, name, content)
                    logger.info("Content from %s stored in database.", url)
                except Exception:
                    logger.exception("Failed to insert main page for %s", start_url)

                links = scrapper.get_links(content)
                for link in links:
                    try:
                        if scrapper.is_url_doc(link) and not db.if_exists_additional(link):
                            additional_content = WebScrapper(link).get_data()
                            db.insert_additional_page(link, start_url, additional_content)
                            logger.info("Additional content from %s stored in database.", link)
                    except Exception:
                        logger.exception("Failed processing additional link %s", link)
            else:
                logger.info("URL %s already exists in the database. Skipping storage.", url)
        except Exception:
            logger.exception("Unexpected error during scrape_and_store for %s", url)
        finally:
            try:
                db.close()
            except Exception:
                logger.exception("Failed to close database connection")

    def prepare_rag(self):
        """Load stored content, chunk it, and add chunks to the RAG collection.

        This method reads all available content from the database, splits
        each document into chunks using `Rag_Handler.chunking`, and adds the
        resulting chunks to the collection via `Rag_Handler.add_document`.
        """
        db = SQDB("web_content.db")
        try:
            contents = db.get_for_chunks()
        except Exception:
            logger.exception("Failed to read contents for chunking")
            contents = []
        finally:
            try:
                db.close()
            except Exception:
                logger.exception("Failed to close database connection")

        rag_handler = Rag_Handler()
        for content in contents:
            try:
                chunks = rag_handler.chunking(content[0], 1000, 200)
                rag_handler.add_document(chunks)
            except Exception:
                logger.exception("Failed to chunk/add document for content id %s", getattr(content, 'id', 'unknown'))
        logger.info("RAG preparation completed.")

    def run(self):
        """Placeholder run loop for orchestrator.

        Implement application-specific orchestration or CLI entrypoints
        here in future iterations.
        """
        try:
            self.scrape_and_store("https://docs.trychroma.com/docs/overview/introduction", "introduction")
        except Exception:
            logger.exception("Orchestrator run failed")
        return

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
