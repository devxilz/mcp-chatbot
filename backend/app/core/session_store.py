import sqlite3
import time

class SessionStore:
    # Initialize the session store with the database path
    def __init__(self, db_path="data/memory_store/memory_session.db"):
        self.db_path = db_path
        self._init_db()
    # Initialize the database and create tables if they don't exist
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS session_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_id TEXT,
                role TEXT,
                text TEXT,
                timestamp INTEGER
            )
        """)

        conn.commit()
        conn.close()

    # Save a message to the database
    def save(self, user_id, session_id, role, text):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO session_messages (user_id, session_id, role, text, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, session_id, role, text, int(time.time())))

        conn.commit()
        conn.close()
    
    # Load messages for a given user and session
    def load(self, user_id, session_id, limit=20):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("""
            SELECT role, text, timestamp
            FROM session_messages
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        """, (user_id, session_id, limit))

        rows = cur.fetchall()
        conn.close()

        messages = []
        for role, text, ts in rows:
            messages.append({
                "role": role,
                "text": text,
                "timestamp": ts
            })

        return messages
    