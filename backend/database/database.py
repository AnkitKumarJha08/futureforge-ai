import sqlite3

conn = sqlite3.connect(
    "futureforge.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""

CREATE TABLE IF NOT EXISTS users(

id INTEGER PRIMARY KEY AUTOINCREMENT,

fullname TEXT NOT NULL,

email TEXT UNIQUE NOT NULL,

password BLOB NOT NULL,

role TEXT DEFAULT 'user'

)

""")

conn.commit()