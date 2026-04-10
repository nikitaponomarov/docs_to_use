import sqlite3
from scraper import WebScrapper
database_name = "web_content.db"
parser = WebScrapper("https://r.jina.ai/docs/overview")
db = sqlite3.connect(database_name)
cursor = db.cursor()


cursor.execute('''DELETE FROM Main_Pages where url = "https://docs.trychroma.com"''')
db.commit()
db.close()
