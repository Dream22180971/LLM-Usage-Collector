import json
from datetime import datetime
from pathlib import Path
from typing import List

from .base import UsageRecord


class QoderCollector:
    """Parse Qoder (Alibaba) session JSONL files for token usage.

    Qoder writes transcripts to ~/.qoder-cn/projects/<project>/<session>.jsonl.
    Only the final assistant chunk (stop_reason set) carries `usage`; streaming
    interim chunks share the same message id and must not be double-counted.
    Token counts currently come back as 0 from the qfmodel gateway (billing is
    credits-based), so zero-token final chunks are still recorded to keep
    request/session counts accurate.
    """

    name = "Qoder"

    def __init__(self):
        self.qoder_dir = Path.home() / ".qoder-cn" / "projects"

    def collect(self) -> List[UsageRecord]:
        records = []
        if not self.qoder_dir.exists():
            return records

        for jsonl_file in self.qoder_dir.rglob("*.jsonl"):
            records.extend(self._parse_session(jsonl_file))
        return records

    def _parse_session(self, path: Path) -> List[UsageRecord]:
        records = []
        session_id = path.stem
        # Parent dir is the encoded project path (e.g. C--Users-33101-Documents-...)
        parent_name = path.parent.name
        project = parent_name.replace("--", "").replace("-", ":") if parent_name else ""

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if obj.get("type") != "assistant":
                        continue

                    msg = obj.get("message", {})
                    if not isinstance(msg, dict):
                        continue

                    # Interim streaming chunks have stop_reason None -> skip
                    if not msg.get("stop_reason"):
                        continue

                    usage = msg.get("usage")
                    if not usage or not isinstance(usage, dict):
                        continue

                    input_tokens = usage.get("input_tokens", 0) or 0
                    output_tokens = usage.get("output_tokens", 0) or 0
                    cache_read = usage.get("cache_read_input_tokens", 0) or 0
                    cache_write = usage.get("cache_creation_input_tokens", 0) or 0

                    model = msg.get("model", "unknown")
                    ts = self._parse_ts(obj.get("timestamp", ""))

                    records.append(UsageRecord(
                        agent=self.name,
                        model=model,
                        timestamp=ts,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cache_read=cache_read,
                        cache_write=cache_write,
                        cost_usd=0.0,  # Qoder bills in credits, not USD
                        session_id=session_id,
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
