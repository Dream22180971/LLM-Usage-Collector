import json
from datetime import datetime
from pathlib import Path
from typing import List

from .base import UsageRecord


class CopilotCollector:
    """Parse GitHub Copilot CLI session.shutdown modelMetrics from events.jsonl."""

    name = "Copilot"

    def __init__(self):
        self.session_state_dir = Path.home() / ".copilot" / "session-state"

    def collect(self) -> List[UsageRecord]:
        records: List[UsageRecord] = []
        if not self.session_state_dir.exists():
            return records

        for events_file in self.session_state_dir.rglob("events.jsonl"):
            records.extend(self._parse_events(events_file))
        return records

    def _parse_events(self, path: Path) -> List[UsageRecord]:
        records: List[UsageRecord] = []
        session_id = path.parent.name
        project = ""
        cwd = ""
        session_start_ms = None

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
                    data = obj.get("data") or {}

                    if otype == "session.start":
                        sid = data.get("sessionId")
                        if sid:
                            session_id = str(sid)
                        ctx = data.get("context") or {}
                        cwd = ctx.get("cwd") or ""
                        project = Path(cwd).name if cwd else ""
                        if not project and ctx.get("repository"):
                            project = str(ctx["repository"])
                        start = data.get("startTime")
                        if start:
                            try:
                                session_start_ms = datetime.fromisoformat(
                                    str(start).replace("Z", "+00:00")
                                )
                            except Exception:
                                pass

                    elif otype == "session.shutdown":
                        ts = self._parse_ts(obj.get("timestamp", ""))
                        if session_start_ms is None and data.get("sessionStartTime"):
                            try:
                                session_start_ms = datetime.fromtimestamp(
                                    float(data["sessionStartTime"]) / 1000
                                )
                            except Exception:
                                pass
                        use_ts = session_start_ms or ts

                        metrics = data.get("modelMetrics") or {}
                        if not isinstance(metrics, dict):
                            continue

                        for model, mm in metrics.items():
                            if not isinstance(mm, dict):
                                continue
                            usage = mm.get("usage") or {}
                            input_tokens = int(usage.get("inputTokens") or 0)
                            output_tokens = int(usage.get("outputTokens") or 0)
                            cache_read = int(usage.get("cacheReadTokens") or 0)
                            cache_write = int(usage.get("cacheWriteTokens") or 0)
                            reasoning = int(usage.get("reasoningTokens") or 0)
                            # OpenAI-style: inputTokens includes cached; keep non-cache input only.
                            input_tokens = max(0, input_tokens - cache_read)
                            if reasoning and reasoning <= output_tokens:
                                pass  # reasoning already counted in output when nested

                            if input_tokens == 0 and output_tokens == 0 and cache_read == 0 and cache_write == 0:
                                continue

                            records.append(UsageRecord(
                                agent=self.name,
                                model=str(model),
                                timestamp=use_ts,
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                                cache_read=cache_read,
                                cache_write=cache_write,
                                cost_usd=0.0,
                                session_id=str(session_id),
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
            return datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
        except Exception:
            return datetime.now()
