import sqlite3
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Database path - can be overridden via env
DB_PATH = os.getenv("DB_PATH", "storage/conversations.db")

class MemoryStore:
    """SQLite-based memory store for conversations"""

    def __init__(self, db_path: str = DB_PATH):
        """Initialize the memory store with SQLite database"""
        # Ensure storage directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self._init_db()
        logger.info(f"MemoryStore initialized with DB at: {db_path}")

    def _init_db(self):
        """Create the conversations table if it doesn't exist"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Create index for faster queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id
            ON conversations(user_id, timestamp)
        """)
        self.conn.commit()

    def save_message(self, user_id: str, role: str, message: str):
        """Save a message to the conversation history"""
        try:
            self.conn.execute(
                "INSERT INTO conversations (user_id, role, message) VALUES (?, ?, ?)",
                (user_id, role, message)
            )
            self.conn.commit()
            logger.debug(f"Saved message for user={user_id}, role={role}")
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            raise RuntimeError(f"Save failed: {e}")

    def load_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Load conversation history for a user"""
        try:
            cursor = self.conn.execute(
                """SELECT role, message, timestamp
                   FROM conversations
                   WHERE user_id = ?
                   ORDER BY timestamp ASC
                   LIMIT ?""",
                (user_id, limit)
            )
            history = [
                {"role": row["role"], "content": row["message"]}
                for row in cursor.fetchall()
            ]
            logger.debug(f"Loaded {len(history)} messages for user={user_id}")
            return history
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []

    def clear_history(self, user_id: str):
        """Clear conversation history for a user"""
        try:
            self.conn.execute(
                "DELETE FROM conversations WHERE user_id = ?",
                (user_id,)
            )
            self.conn.commit()
            logger.info(f"Cleared history for user={user_id}")
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            raise RuntimeError(f"Clear failed: {e}")

    def get_stats(self, user_id: str) -> Dict:
        """Get conversation statistics for a user"""
        try:
            cursor = self.conn.execute(
                """SELECT
                    COUNT(*) as total_messages,
                    COUNT(DISTINCT DATE(timestamp)) as active_days
                   FROM conversations
                   WHERE user_id = ?""",
                (user_id,)
            )
            row = cursor.fetchone()
            return {
                "total_messages": row["total_messages"],
                "active_days": row["active_days"]
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"total_messages": 0, "active_days": 0}

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


# Global instance for backward compatibility
_store: Optional[MemoryStore] = None

def get_store() -> MemoryStore:
    """Get or create the global MemoryStore instance"""
    global _store
    if _store is None:
        _store = MemoryStore()
    return _store


# Backward-compatible function-based API
def save_message(user_id: str, role: str, message: str):
    """Save a message (backward-compatible API)"""
    store = get_store()
    store.save_message(user_id, role, message)


def load_history(user_id: str, limit: int = 10) -> list:
    """Load conversation history (backward-compatible API)"""
    store = get_store()
    return store.load_history(user_id, limit)


def clear_history(user_id: str):
    """Clear conversation history (backward-compatible API)"""
    store = get_store()
    store.clear_history(user_id)
