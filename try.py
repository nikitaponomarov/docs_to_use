import sqlite3
from scraper import WebScrapper
database_name = "web_content.db"
parser = WebScrapper("https://r.jina.ai/docs/overview")
db = sqlite3.connect(database_name)
cursor = db.cursor()


cursor.execute('''DELETE FROM Additional_Pages
    WHERE rowid NOT IN (
    SELECT MIN(rowid)
    FROM Additional_Pages
    GROUP BY content
);''')
db.commit()
db.close()
