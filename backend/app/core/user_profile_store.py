# app/core/user_profile_store.py

import json
import sqlite3
import time
from app.core.settings import settings
import os

DB_PATH = settings.PROFILE_DB_PATH

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)



class UserProfileStore:
    def __init__(self):
        self.db_path = DB_PATH
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                user_id TEXT PRIMARY KEY,
                profile_json TEXT,
                updated_at INTEGER
            )
        """)
        self.conn.commit()

    # ----------------------------------------------------------
    # Save or update user profile
    # ----------------------------------------------------------
    def save_profile(self, user_id: str, profile: dict):
        now = int(time.time())
        profile_json = json.dumps(profile)

        self.conn.execute("""
            INSERT INTO user_profile (user_id, profile_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET profile_json=excluded.profile_json,
                          updated_at=excluded.updated_at
        """, (user_id, profile_json, now))

        self.conn.commit()

    # ----------------------------------------------------------
    # Load profile
    # ----------------------------------------------------------
    def load_profile(self, user_id: str):
        cur = self.conn.execute(
            "SELECT profile_json FROM user_profile WHERE user_id=?",
            (user_id,)
        )
        row = cur.fetchone()

        if not row:
            return None

        return json.loads(row[0])

    # ----------------------------------------------------------
    # Update only one field
    # ----------------------------------------------------------
    def update_field(self, user_id: str, field: str, value):
        profile = self.load_profile(user_id) or {}
        profile[field] = value
        self.save_profile(user_id, profile)
