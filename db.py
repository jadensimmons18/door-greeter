import sqlite3

conn = sqlite3.connect("faces.db")   # opens the file, creating it if needed
conn.execute("CREATE TABLE IF NOT EXISTS faces (id INTEGER PRIMARY KEY, name TEXT, embedding BLOB)")
conn.commit()                        # saves your changes to the file
conn.close()


