import sqlite3


class SQDB:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Main_Pages
                            (url TEXT NOT NULL,
                            name TEXT,
                            content TEXT,
                            constraint main_pk primary key (url, name))''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Additional_Pages
                            (url_a TEXT constraint urla_pk primary key NOT NULL,
                            url_mn TEXT,
                            content TEXT,
                            foreign key (url_mn) references Main_Pages(url))''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS COLLECTIONS
                            (name TEXT PRIMARY KEY NOT NULL,
                            collection_name TEXT NOT NULL,
                            embed_model TEXT,
                            embed_url TEXT)''')
        # migrate existing DBs that don't have the new columns yet
        for col in ("embed_model", "embed_url"):
            try:
                self.cursor.execute(f"ALTER TABLE COLLECTIONS ADD COLUMN {col} TEXT")
            except Exception:
                pass
        self.conn.commit()

    def insert_main_page(self, url, name, content):
        self.cursor.execute(
            "INSERT INTO Main_Pages (url, name, content) VALUES (?, ?, ?)",
            (url, name, content),
        )
        self.conn.commit()

    def insert_additional_page(self, url_a, url_mn, content):
        self.cursor.execute(
            "INSERT INTO Additional_Pages (url_a, url_mn, content) VALUES (?, ?, ?)",
            (url_a, url_mn, content),
        )
        self.conn.commit()

    def insert_collection(self, name, collection_name, embed_model=None, embed_url=None):
        try:
            self.cursor.execute(
                "INSERT OR IGNORE INTO COLLECTIONS (name, collection_name, embed_model, embed_url) VALUES (?, ?, ?, ?)",
                (name, collection_name, embed_model, embed_url),
            )
            self.conn.commit()
        except Exception:
            pass

    def close(self):
        self.conn.close()

    def get_for_chunks(self, name):
        self.cursor.execute("SELECT content FROM Main_Pages WHERE name = ?", (name,))
        main_contents = self.cursor.fetchall()
        self.cursor.execute(
            "SELECT content FROM Additional_Pages WHERE url_mn = (SELECT url FROM Main_Pages WHERE name = ?)",
            (name,),
        )
        additional_contents = self.cursor.fetchall()
        return main_contents + additional_contents

    def get_collection_name(self, name):
        self.cursor.execute("SELECT collection_name FROM COLLECTIONS WHERE name = ?", (name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_embed_config(self, name):
        """Return (embed_model, embed_url) stored for this library, or (None, None)."""
        self.cursor.execute(
            "SELECT embed_model, embed_url FROM COLLECTIONS WHERE name = ?", (name,)
        )
        result = self.cursor.fetchone()
        return (result[0], result[1]) if result else (None, None)

    def if_exists_main(self, url):
        self.cursor.execute("SELECT 1 FROM Main_Pages WHERE url = ?", (url,))
        return self.cursor.fetchone() is not None

    def if_exists_collection(self, name):
        """Check whether a library has been fully learned (has a collection entry)."""
        self.cursor.execute("SELECT 1 FROM COLLECTIONS WHERE name = ?", (name,))
        return self.cursor.fetchone() is not None

    def if_exists_additional(self, url_a):
        self.cursor.execute("SELECT 1 FROM Additional_Pages WHERE url_a = ?", (url_a,))
        return self.cursor.fetchone() is not None
