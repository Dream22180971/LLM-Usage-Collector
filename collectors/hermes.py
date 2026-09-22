import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List

from .base import UsageRecord


class HermesCollector:
    """Parse Hermes (Desktop + Terminal) state.db for token usage."""

    name = "Hermes"

    def __init__(self):
        local_app = Path(os.environ.get("LOCALAPPDATA", ""))
        self.sources = []

        # Desktop version
        desktop_db = local_app / "Hermes Agent CN Desktop" / "data" / "hermes-home" / "state.db"
        if desktop_db.exists():
            self.sources.append(("Hermes-Desktop", desktop_db))

        # Terminal version
        terminal_db = local_app / "hermes" / "state.db"
        if terminal_db.exists():
            self.sources.append(("Hermes-Terminal", terminal_db))

    def collect(self) -> List[UsageRecord]:
        records = []
        for label, db_path in self.sources:
            records.extend(self._parse_db(db_path, label))
        return records

    def _parse_db(self, db_path: Path, source_label: str) -> List[UsageRecord]:
        records = []
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Query session_model_usage for per-model breakdown
            cursor.execute("""
                SELECT session_id, model, input_tokens, output_tokens,
                       cache_read_tokens, cache_write_tokens, reasoning_tokens,
                       estimated_cost_usd, first_seen, last_seen
                FROM session_model_usage
            """)

            for row in cursor.fetchall():
                (session_id, model, input_tokens, output_tokens,
                 cache_read, cache_write, reasoning,
                 cost, first_seen, last_seen) = row

                input_tokens = input_tokens or 0
                output_tokens = output_tokens or 0
                cache_read = cache_read or 0
                cache_write = cache_write or 0
                cost = cost or 0.0

                if input_tokens == 0 and output_tokens == 0:
                    continue

                # Use last_seen as timestamp (unix float)
                ts = datetime.now()
                if last_seen:
                    try:
                        ts = datetime.fromtimestamp(last_seen)
                    except Exception:
                        pass

                # Build model label
                model_label = model or "unknown"

                records.append(UsageRecord(
                    agent=f"{self.name} ({source_label})",
                    model=model_label,
                    timestamp=ts,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cache_read=cache_read,
                    cache_write=cache_write,
                    cost_usd=cost,
                    session_id=str(session_id),
                    project=f"session:{session_id}",
                ))

            conn.close()
        except Exception as e:
            print(f"  [Hermes] Error reading {db_path}: {e}")
        return records
