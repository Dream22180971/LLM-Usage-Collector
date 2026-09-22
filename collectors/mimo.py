import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .base import UsageRecord


class MimoCollector:
    """Parse MiMo Desktop mimocode.db assistant message token usage."""

    name = "MiMo Desktop"

    def __init__(self):
        # MIMOCODE_HOME overrides XDG data dir; default ~/.local/share/mimocode
        home = os.environ.get("MIMOCODE_HOME")
        if home:
            data_dir = Path(home)
        else:
            data_dir = Path.home() / ".local" / "share" / "mimocode"
        self.db_path = data_dir / "mimocode.db"

    def collect(self) -> List[UsageRecord]:
        records: List[UsageRecord] = []
        if not self.db_path.exists():
            return records

        # Copy DB (+WAL/SHM) so we never lock the live desktop engine
        tmp = tempfile.mktemp(prefix="mimocode_usage_", suffix=".db")
        try:
            shutil.copy2(self.db_path, tmp)
            for ext in ("-wal", "-shm"):
                src = Path(str(self.db_path) + ext)
                if src.exists():
                    shutil.copy2(src, str(tmp) + ext)

            conn = sqlite3.connect(tmp)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT m.session_id, m.data, s.directory
                    FROM message m
                    LEFT JOIN session s ON s.id = m.session_id
                    WHERE m.data LIKE '%"role":"assistant"%'
                      AND m.data LIKE '%"tokens"%'
                    """
                )
                for session_id, data, directory in cursor.fetchall():
                    rec = self._parse_message(data, session_id, directory)
                    if rec:
                        records.append(rec)
            finally:
                conn.close()
        except Exception as e:
            print(f"  [{self.name}] Error: {e}")
        finally:
            for p in (tmp, str(tmp) + "-wal", str(tmp) + "-shm"):
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
        return records

    def _parse_message(self, data, session_id, directory) -> Optional[UsageRecord]:
        try:
            obj = json.loads(data) if isinstance(data, str) else data
        except Exception:
            return None
        if not isinstance(obj, dict) or obj.get("role") != "assistant":
            return None

        tokens = obj.get("tokens") or {}
        if not isinstance(tokens, dict):
            return None

        cache = tokens.get("cache") or {}
        if not isinstance(cache, dict):
            cache = {}

        input_tokens = int(tokens.get("input") or 0)
        output_tokens = int(tokens.get("output") or 0)
        reasoning = int(tokens.get("reasoning") or 0)
        cache_read = int(cache.get("read") or 0)
        cache_write = int(cache.get("write") or 0)
        output_tokens += reasoning

        if input_tokens == 0 and output_tokens == 0 and cache_read == 0 and cache_write == 0:
            return None

        model_id = obj.get("modelID") or "unknown"
        provider_id = obj.get("providerID") or ""
        model = f"{provider_id}/{model_id}" if provider_id else model_id

        ts = datetime.now()
        time_obj = obj.get("time") or {}
        created = None
        if isinstance(time_obj, dict):
            created = time_obj.get("created")
        if created:
            try:
                # epoch ms
                ts = datetime.fromtimestamp(float(created) / 1000)
            except Exception:
                pass

        cost = obj.get("cost") or 0
        try:
            cost = float(cost)
        except Exception:
            cost = 0.0

        return UsageRecord(
            agent=self.name,
            model=model,
            timestamp=ts,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read=cache_read,
            cache_write=cache_write,
            cost_usd=cost,
            session_id=str(session_id or ""),
            project=str(directory or ""),
        )
