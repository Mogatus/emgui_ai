"""Database access layer for Neon PostgreSQL."""

from datetime import datetime, timedelta
from typing import Optional

import psycopg2
import psycopg2.extras

from src.utils.config import DBConfig


class Database:
    """Manages the connection to the Neon PostgreSQL database."""

    def __init__(self):
        self._conn = None

    # -- connection management ------------------------------------------------

    def connect(self):
        """Open a connection (reuses existing if still alive)."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(DBConfig.connection_string())
        return self._conn

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()

    # -- queries --------------------------------------------------------------

    def fetch_data(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 5000,
    ) -> list[dict]:
        """Return meter_data rows as list of dicts.

        Parameters
        ----------
        start : datetime, optional
            Begin of time window (inclusive).
        end : datetime, optional
            End of time window (inclusive).
        limit : int
            Maximum number of rows returned.
        """
        conn = self.connect()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            query = "SELECT id, loadval, pv, grid_feed_in, grid_purchase, savetimestamp FROM meter_data"
            conditions = []
            params: list = []

            if start:
                conditions.append("savetimestamp >= %s")
                params.append(str(start))
            if end:
                conditions.append("savetimestamp <= %s")
                params.append(str(end))

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY savetimestamp ASC LIMIT %s"
            params.append(limit)

            cur.execute(query, params)
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def fetch_latest(self, n: int = 1) -> list[dict]:
        """Fetch the *n* most recent rows."""
        conn = self.connect()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, loadval, pv, grid_feed_in, grid_purchase, savetimestamp "
                "FROM meter_data ORDER BY savetimestamp DESC LIMIT %s",
                (n,),
            )
            rows = cur.fetchall()
        return [dict(r) for r in rows]

    def fetch_date_range(self) -> tuple[Optional[str], Optional[str]]:
        """Return (min_timestamp, max_timestamp) in the table."""
        conn = self.connect()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MIN(savetimestamp), MAX(savetimestamp) FROM meter_data"
            )
            row = cur.fetchone()
        if row:
            return row[0], row[1]
        return None, None
