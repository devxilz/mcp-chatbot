import sqlite3
import time
from app.core.settings import settings
import os

DB_PATH = settings.SESSION_DB_PATH

# Ensure folder exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

class SessionStore:

    def __init__(self):
        # Instance-level path
        self.db_path = DB_PATH
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
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

    def save(self, user_id, session_id, role, text):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO session_messages (user_id, session_id, role, text, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, session_id, role, text, int(time.time())))

        conn.commit()
        conn.close()

    def load(self, user_id, session_id, limit=20):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cur = conn.cursor()

        cur.execute("""
            SELECT role, text, timestamp
            FROM session_messages
            WHERE user_id = ? AND session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, session_id, limit))

        rows = cur.fetchall()
        conn.close()

        return [
            {"role": role, "text": text, "timestamp": ts}
            for role, text, ts in rows
        ]
