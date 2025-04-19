import sqlite3
from datetime import datetime, timedelta

class ConversationDatabase:
    def __init__(self, db_name="conversations.db"):
        # Conecta ao banco de dados SQLite (ou cria o arquivo se não existir)
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        # Cria a tabela 'conversations' caso não exista
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    user_id TEXT,
                    guild_id TEXT,
                    message TEXT,
                    timestamp DATETIME,
                    PRIMARY KEY (user_id, guild_id, timestamp)
                )
            """)

    def save_message(self, user_id, guild_id, message):
        # Salva ou atualiza a mensagem do usuário no banco de dados
        with self.conn:
            self.conn.execute("""
                INSERT OR REPLACE INTO conversations (user_id, guild_id, message, timestamp)
                VALUES (?, ?, ?, ?)
            """, (user_id, guild_id, message, datetime.now()))

    def get_context(self, user_id, guild_id, time_limit_hours=1):
        # Recupera as mensagens anteriores de um usuário dentro do intervalo de tempo (em horas)
        cutoff = datetime.now() - timedelta(hours=time_limit_hours)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT message FROM conversations
            WHERE user_id = ? AND guild_id = ? AND timestamp > ?
            ORDER BY timestamp ASC
        """, (user_id, guild_id, cutoff))
        return [row[0] for row in cursor.fetchall()]

    def clear_context(self, user_id, guild_id):
        # Deleta todas as mensagens de um usuário para um servidor específico
        with self.conn:
            self.conn.execute("""
                DELETE FROM conversations
                WHERE user_id = ? AND guild_id = ?
            """, (user_id, guild_id))
