import sqlite3
from scraper import WebScrapper
database_name = "web_content.db"
parser = WebScrapper("https://r.jina.ai/docs/overview")
db = sqlite3.connect(database_name)
cursor = db.cursor()

cursor.execute('''SELECT url_a FROM Additional_Pages''')
urls  = cursor.fetchall()
for url in urls:
    if not parser.is_url_doc(url[0]):
        cursor.execute('''DELETE FROM Additional_Pages WHERE url_a = ?''', (url[0],))
        db.commit()
db.close()
