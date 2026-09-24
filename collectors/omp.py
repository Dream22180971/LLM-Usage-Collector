import json
from datetime import datetime
from pathlib import Path
from typing import List

from .base import UsageRecord


class OmpCollector:
    """Parse Oh My Pi (omp) session JSONL files for token usage."""

    name = "OMP"

    def __init__(self):
        self.omp_dir = Path.home() / ".omp" / "agent" / "sessions"

    def collect(self) -> List[UsageRecord]:
        records = []
        if not self.omp_dir.exists():
            return records

        for jsonl_file in self.omp_dir.rglob("*.jsonl"):
            records.extend(self._parse_session(jsonl_file))
        return records

    def _parse_session(self, path: Path) -> List[UsageRecord]:
        records = []
        session_id = path.stem
        # Fallback project from parent dir name (e.g. -AppData-Local-Temp)
        parent_name = path.parent.name
        fallback_project = parent_name.replace("-", ":").lstrip(":") if parent_name else ""
        project = fallback_project

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

                    otype = obj.get("type")
                    if otype == "session":
                        cwd = obj.get("cwd", "")
                        if cwd:
                            project = Path(cwd).name or fallback_project
                        continue

                    if otype != "message":
                        continue

                    msg = obj.get("message", {})
                    if not isinstance(msg, dict):
                        continue
                    if msg.get("role") != "assistant":
                        continue

                    usage = msg.get("usage")
                    if not usage or not isinstance(usage, dict):
                        continue

                    input_tokens = usage.get("input", 0) or 0
                    output_tokens = usage.get("output", 0) or 0
                    cache_read = usage.get("cacheRead", 0) or 0
                    cache_write = usage.get("cacheWrite", 0) or 0

                    if input_tokens == 0 and output_tokens == 0:
                        continue

                    model = msg.get("model", "unknown")
                    cost_data = usage.get("cost", {})
                    cost_total = cost_data.get("total", 0) if isinstance(cost_data, dict) else 0

                    ts = self._parse_ts(obj.get("timestamp", ""))

                    records.append(UsageRecord(
                        agent=self.name,
                        model=model,
                        timestamp=ts,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cache_read=cache_read,
                        cache_write=cache_write,
                        cost_usd=cost_total,
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
