import json
import os
from datetime import datetime
from pathlib import Path
from typing import List

from .base import UsageRecord


class ClaudeCollector:
    """Parse Claude Code session JSONL files for token usage."""

    name = "Claude Code"

    def __init__(self):
        self.claude_dir = Path.home() / ".claude"

    def collect(self) -> List[UsageRecord]:
        records = []
        projects_dir = self.claude_dir / "projects"
        if not projects_dir.exists():
            return records

        for jsonl_file in projects_dir.rglob("*.jsonl"):
            # Skip subagent files
            if "subagents" in str(jsonl_file):
                continue
            records.extend(self._parse_session(jsonl_file))
        return records

    def _parse_session(self, path: Path) -> List[UsageRecord]:
        records = []
        session_id = path.stem
        # Extract project name from parent dir
        project = path.parent.name

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

                    usage = msg.get("usage")
                    if not usage or not isinstance(usage, dict):
                        continue

                    input_tokens = usage.get("input_tokens", 0) or 0
                    output_tokens = usage.get("output_tokens", 0) or 0
                    cache_read = usage.get("cache_read_input_tokens", 0) or 0
                    cache_write = usage.get("cache_creation_input_tokens", 0) or 0

                    if input_tokens == 0 and output_tokens == 0:
                        continue

                    model = msg.get("model", "unknown")
                    ts_str = obj.get("timestamp", "")
                    ts = self._parse_ts(ts_str)

                    records.append(UsageRecord(
                        agent=self.name,
                        model=model,
                        timestamp=ts,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cache_read=cache_read,
                        cache_write=cache_write,
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
            # Handle Z suffix and milliseconds
            ts_str = ts_str.replace("Z", "+00:00")
            return datetime.fromisoformat(ts_str)
        except Exception:
            return datetime.now()
