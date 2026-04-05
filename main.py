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
        content = scrapper.get_data()
        db = SQDB("web_content.db")
        db.create_table()
        if not db.if_exists_main(url):

            db.insert_main_page(url, name,content)
            print(f"Content from {url} stored in database.")
            if not db.if_exists_additional:
                links = scrapper.get_links(content)
                for link in links:
                    if not db.if_exists_main(link):
                        additional_content = WebScrapper(link).get_data()
                        db.insert_additional_page(link, url, additional_content)
                        print(f"Additional content from {link} stored in database.")
        else:
            print(f"URL {url} already exists in the database. Skipping storage.")
        db.close()

    def prepare_rag(self):
        """Load stored content, chunk it, and add chunks to the RAG collection.

        This method reads all available content from the database, splits
        each document into chunks using `Rag_Handler.chunking`, and adds the
        resulting chunks to the collection via `Rag_Handler.add_document`.
        """
        db = SQDB("web_content.db")
        contents = db.get_for_chunks()
        db.close()
        rag_handler = Rag_Handler()
        for content in contents:
            chunks = rag_handler.chunking(content[0], 1000, 200)
            rag_handler.add_document(chunks)
        print("RAG preparation completed.")

    def run(self):
        """Placeholder run loop for orchestrator.

        Implement application-specific orchestration or CLI entrypoints
        here in future iterations.
        """
        self.scrape_and_store("https://docs.trychroma.com/docs/overview/introduction")

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
