import sqlite3

class SQDB:
    """SQLite helper for storing scraped web content and related records.

    This class provides simple convenience methods to create the schema,
    insert main and additional pages, query stored content for chunking,
    and check for existence of a URL.

    Attributes:
        db_name (str): Path to the SQLite database file.
        conn (sqlite3.Connection): SQLite connection object.
        cursor (sqlite3.Cursor): Cursor for executing SQL statements.
    """

    def __init__(self, db_name):
        """Initialize the database connection.

        Args:
            db_name (str): Filename or path of the SQLite database to open.
        """
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
    def create_table(self):
        """Create required tables if they don't already exist.

        The schema includes `Main_Pages` for primary documents and
        `Additional_Pages` for linked/auxiliary pages referencing the main
        page.
        """
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Main_Pages
                            (url TEXT NOT NULL,
                            name TEXT,
                            content TEXT,
                            constraint main_pk primary key (url, name)
                            )''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Additional_Pages
                            (url_a TEXT constraint urla_pk primary key NOT NULL,
                            url_mn TEXT,
                            content TEXT,
                            foreign key (url_mn) references Main_Pages(url))''')
        self.conn.commit()

    def insert_main_page(self, url, name, content):
        """Insert a main page record into the database.

        Args:
            url (str): The unique URL of the main page.
            name (str): The name of the main page.
            content (str): The textual content of the page.
        """
        self.cursor.execute("INSERT INTO Main_Pages (url, name, content) VALUES (?, ?, ?)", (url, name, content))
        self.conn.commit()

    def insert_additional_page(self, url_a, url_mn, content):
        """Insert an additional/auxiliary page linked to a main page.

        Args:
            url_a (str): Unique URL of the additional page.
            url_mn (str): Foreign-key URL referencing the main page.
            content (str): The textual content of the additional page.
        """
        self.cursor.execute("INSERT INTO Additional_Pages (url_a, url_mn, content) VALUES (?, ?, ?)", (url_a, url_mn, content))
        self.conn.commit()

    def close(self):
        """Close the underlying SQLite connection.

        Call this when database operations are complete to release resources.
        """
        self.conn.close()

    def get_for_chunks(self, name):
        """Retrieve all stored content suitable for chunking.

        Returns:
            list: Combined list of tuples containing content strings from both
                  `Main_Pages` and `Additional_Pages`.
        """
        self.cursor.execute("SELECT content FROM Main_Pages where name = ?", (name,))
        main_contents = self.cursor.fetchall()
        self.cursor.execute("SELECT content FROM Additional_Pages where name = ?", (name,))
        additional_contents = self.cursor.fetchall()
        return main_contents + additional_contents
    
    def if_exists_main(self, url):
        """Check whether a URL already exists in the Main_Pages table.

        Args:
            url (str): URL to check for existence.

        Returns:
            bool: True if the URL exists in `Main_Pages`.
        """
        self.cursor.execute("SELECT 1 FROM Main_Pages WHERE url = ?", (url,))
        return self.cursor.fetchone() is not None
    def if_exists_additional(self, url_a):
        """Check whether a URL already exists in the Additional_Pages table.

        Args:
            url_a (str): URL to check for existence.

        Returns:
            bool: True if the URL exists in `Additional_Pages`.
        """
        self.cursor.execute("SELECT 1 FROM Additional_Pages WHERE url_a = ?", (url_a,))
        return self.cursor.fetchone() is not None