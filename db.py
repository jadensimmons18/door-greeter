import sqlite3
import numpy as np


def init_db():
    conn = sqlite3.connect("faces.db")   # opens the file, creating it if needed
    conn.execute("CREATE TABLE IF NOT EXISTS faces (id INTEGER PRIMARY KEY, name TEXT, embedding BLOB)")
    conn.commit()                        # saves your changes to the file
    conn.close()


def save_face(name, embedding):
    conn = sqlite3.connect("faces.db")
    conn.execute(
        "INSERT INTO faces (name, embedding) VALUES (?, ?)",
        (name, embedding.tobytes()),
    )
    conn.commit()
    conn.close()

# returns an array of all known faces in the database
def load_faces():
    conn = sqlite3.connect("faces.db")
    rows = conn.execute("SELECT name, embedding FROM faces").fetchall()
    conn.close()

    known = []
    for name, blob in rows:
        embedding = np.frombuffer(blob, dtype=np.float32).reshape(1, 128)
        known.append((name, embedding))
    return known