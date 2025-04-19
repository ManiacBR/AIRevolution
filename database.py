import sqlite3
from datetime import datetime, timedelta

class ConversationDatabase:
    def __init__(self, db_name="conversations.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    user_id TEXT,
                    channel_id TEXT,
                    message TEXT,
                    timestamp DATETIME,
                    PRIMARY KEY (user_id, channel_id)
                )
            """)

    def save_message(self, user_id, channel_id, message):
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO conversations (user_id, channel_id, message, timestamp)
                VALUES (?, ?, ?, ?)
            """, (user_id, channel_id, message, datetime.now()))

    def get_context(self, user_id, channel_id, time_limit_hours=1):
        cutoff = datetime.now() - timedelta(hours=time_limit_hours)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT message FROM conversations
            WHERE user_id = ? AND channel_id = ? AND timestamp > ?
            ORDER BY timestamp ASC
        """, (user_id, channel_id, cutoff))
        return [row[0] for row in cursor.fetchall()]

    def clear_context(self, user_id, channel_id):
        with self.conn:
            self.conn.execute("""
                DELETE FROM conversations
                WHERE user_id = ? AND channel_id = ?
            """, (user_id, channel_id))
