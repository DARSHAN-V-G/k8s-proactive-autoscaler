"""
Local Metrics History Persistence (SQLite)
Maintains historical time-series sequence Seq[] for the GRU Evaluator.
"""

import os
import sqlite3
import time
from typing import List, Tuple, Optional


class MetricsDatabase:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get("METRICS_DB_PATH", "/tmp/metrics.db")
        self.db_path = db_path
        
        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    avg_u REAL NOT NULL,
                    cur_r INTEGER NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics_history(timestamp)")
            conn.commit()

    def insert_metric(self, avg_u: float, cur_r: int, timestamp: Optional[float] = None) -> int:
        """Inserts a new metric observation and returns row id."""
        if timestamp is None:
            timestamp = time.time()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO metrics_history (timestamp, avg_u, cur_r) VALUES (?, ?, ?)",
                (float(timestamp), float(avg_u), int(cur_r))
            )
            conn.commit()
            return cursor.lastrowid

    def get_recent_sequence(self, n_steps: int = 24) -> List[float]:
        """
        Returns the last n_steps average CPU values in chronological order (oldest to newest).
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT avg_u FROM metrics_history ORDER BY id DESC LIMIT ?",
                (int(n_steps),)
            )
            rows = cursor.fetchall()
            # Reverse to get chronological order
            return [r[0] for r in reversed(rows)]

    def get_sequence_length(self) -> int:
        """Returns the total number of recorded metric observations."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM metrics_history")
            return cursor.fetchone()[0]

    def prune_old_records(self, keep_last: int = 1000) -> None:
        """Keeps only the most recent records to prevent unbounded database growth."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM metrics_history 
                WHERE id NOT IN (
                    SELECT id FROM metrics_history ORDER BY id DESC LIMIT ?
                )
            """, (int(keep_last),))
            conn.commit()

    def clear(self) -> None:
        """Clears all records from the database (useful for testing)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM metrics_history")
            conn.commit()
