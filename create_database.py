import sqlite3
import os

os.makedirs("data", exist_ok=True)

connection = sqlite3.connect("data/comiccraft.db")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS comics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    prompt TEXT,
    story TEXT,
    genre TEXT,
    characters TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

connection.commit()
connection.close()

print("Database created successfully!")