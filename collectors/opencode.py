import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import List

from .base import UsageRecord


class OpenCodeCollector:
    """Parse OpenCode session table for token usage."""

    name = "OpenCode"

    def __init__(self):
        self.db_path = Path.home() / ".local" / "share" / "opencode" / "opencode.db"

    def collect(self) -> List[UsageRecord]:
        records = []
        if not self.db_path.exists():
            return records

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, model, tokens_input, tokens_output,
                       tokens_cache_read, tokens_cache_write, tokens_reasoning,
                       cost, time_created, directory
                FROM session
            """)

            for row in cursor.fetchall():
                (session_id, model_json, tokens_input, tokens_output,
                 cache_read, cache_write, reasoning,
                 cost, time_created, directory) = row

                tokens_input = tokens_input or 0
                tokens_output = tokens_output or 0
                cache_read = cache_read or 0
                cache_write = cache_write or 0
                cost = cost or 0.0

                if tokens_input == 0 and tokens_output == 0:
                    continue

                # Parse model JSON: {"id":"glm-5.3","providerID":"zhipuai","variant":"default"}
                model_name = "unknown"
                if model_json:
                    try:
                        import json
                        m = json.loads(model_json) if isinstance(model_json, str) else model_json
                        model_name = m.get("id", "unknown")
                    except Exception:
                        model_name = str(model_json)

                # time_created is epoch ms
                ts = datetime.now()
                if time_created:
                    try:
                        ts = datetime.fromtimestamp(time_created / 1000)
                    except Exception:
                        pass

                records.append(UsageRecord(
                    agent=self.name,
                    model=model_name,
                    timestamp=ts,
                    input_tokens=tokens_input,
                    output_tokens=tokens_output,
                    cache_read=cache_read,
                    cache_write=cache_write,
                    cost_usd=cost,
                    session_id=str(session_id),
                    project=directory or "",
                ))

            conn.close()
        except Exception as e:
            print(f"  [{self.name}] Error: {e}")
        return records
