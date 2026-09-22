import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import List

from .base import UsageRecord


class ZCodeCollector:
    """Parse ZCode (智谱) model_usage table for token usage."""

    name = "ZCode"

    def __init__(self):
        self.db_path = Path.home() / ".zcode" / "cli" / "db" / "db.sqlite"

    def collect(self) -> List[UsageRecord]:
        records = []
        if not self.db_path.exists():
            return records

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # model_usage has per-request token data
            cursor.execute("""
                SELECT session_id, model_id, provider_id, agent,
                       input_tokens, output_tokens, reasoning_tokens,
                       cache_creation_input_tokens, cache_read_input_tokens,
                       started_at, completed_at, status, duration_ms
                FROM model_usage
            """)

            for row in cursor.fetchall():
                (session_id, model_id, provider_id, agent,
                 input_tokens, output_tokens, reasoning,
                 cache_creation, cache_read,
                 started_at, completed_at, status, duration_ms) = row

                input_tokens = input_tokens or 0
                output_tokens = output_tokens or 0
                cache_read = cache_read or 0
                cache_write = cache_creation or 0

                if input_tokens == 0 and output_tokens == 0:
                    continue

                # started_at is epoch ms
                ts = datetime.now()
                if started_at:
                    try:
                        ts = datetime.fromtimestamp(started_at / 1000)
                    except Exception:
                        pass

                model_name = model_id or "unknown"

                records.append(UsageRecord(
                    agent=self.name,
                    model=model_name,
                    timestamp=ts,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cache_read=cache_read,
                    cache_write=cache_write,
                    session_id=str(session_id),
                    project=f"provider:{provider_id}",
                ))

            conn.close()
        except Exception as e:
            print(f"  [{self.name}] Error: {e}")
        return records
