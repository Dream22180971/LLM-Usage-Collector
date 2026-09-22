import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .base import UsageRecord


class CodexCollector:
    """Parse Codex session rollout JSONL files for token usage."""

    name = "Codex"

    def __init__(self):
        self.sessions_dir = Path.home() / ".codex" / "sessions"

    def collect(self) -> List[UsageRecord]:
        records: List[UsageRecord] = []
        if not self.sessions_dir.exists():
            return records

        for jsonl_file in self.sessions_dir.rglob("rollout-*.jsonl"):
            records.extend(self._parse_session(jsonl_file))
        return records

    def _parse_session(self, path: Path) -> List[UsageRecord]:
        records: List[UsageRecord] = []
        session_id = path.stem
        # rollout-2026-09-22T11-07-08-<uuid> -> extract uuid if present
        parts = path.stem.split("-", 3)
        if len(parts) == 4:
            session_id = parts[3]

        model = "unknown"
        project = ""
        cwd = ""

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    otype = obj.get("type")
                    payload = obj.get("payload")
                    if not isinstance(payload, dict):
                        continue

                    if otype == "session_meta":
                        sid = payload.get("session_id") or payload.get("id")
                        if sid:
                            session_id = sid
                        cwd = payload.get("cwd") or ""
                        project = Path(cwd).name if cwd else ""
                        prov = payload.get("base_instructions")
                        if isinstance(prov, dict):
                            m = (prov.get("provenance") or {}).get("model")
                            if m:
                                model = m

                    elif otype == "world_state":
                        state = payload.get("state") or {}
                        cm = state.get("collaboration_mode") or {}
                        m = cm.get("model") or state.get("model")
                        if m:
                            model = m

                    elif otype == "turn_context":
                        m = payload.get("model")
                        if m:
                            model = m
                        if not project and payload.get("cwd"):
                            project = Path(payload["cwd"]).name

                    elif otype == "token_usage_record":
                        usage = payload.get("usage")
                        if not isinstance(usage, dict):
                            continue

                        input_total = usage.get("input_tokens", 0) or 0
                        cache_read = usage.get("cached_input_tokens", 0) or 0
                        cache_write = usage.get("cache_write_input_tokens", 0) or 0
                        output = usage.get("output_tokens", 0) or 0

                        # cached is a subset of input; subtract to avoid double-count
                        input_tokens = max(0, input_total - cache_read)

                        if input_tokens == 0 and output == 0 and cache_read == 0:
                            continue

                        ts = self._parse_ts(obj.get("timestamp", ""))
                        sid = payload.get("session_id") or session_id

                        records.append(UsageRecord(
                            agent=self.name,
                            model=model,
                            timestamp=ts,
                            input_tokens=input_tokens,
                            output_tokens=output,
                            cache_read=cache_read,
                            cache_write=cache_write,
                            cost_usd=0.0,
                            session_id=str(sid),
                            project=project,
                        ))
        except Exception:
            pass
        return records

    @staticmethod
    def _parse_ts(ts_str: str) -> datetime:
        if not ts_str:
            return datetime.now()
        try:
            ts_str = ts_str.replace("Z", "+00:00")
            return datetime.fromisoformat(ts_str)
        except Exception:
            return datetime.now()
