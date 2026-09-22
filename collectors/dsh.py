import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .base import UsageRecord


class DshCollector:
    """Parse DeepSeek Harness (DSH) session token usage from session_projcache.json."""

    name = "DSH"

    def __init__(self):
        self.storage_path = Path.home() / ".dsh" / "storages" / "session_projcache.json"
        self.sessions_dir = Path.home() / ".dsh" / "sessions"

    def collect(self) -> List[UsageRecord]:
        records: List[UsageRecord] = []
        if not self.storage_path.exists():
            return records

        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except Exception:
            return records

        sessions = (data.get("tables") or {}).get("sessions") or {}
        for session_id, entry in sessions.items():
            rec = self._parse_session(session_id, entry)
            if rec:
                records.append(rec)
        return records

    def _parse_session(self, session_id: str, entry: dict) -> Optional[UsageRecord]:
        rows = entry.get("rows") or {}
        token_usage = ((rows.get("tokenUsage") or {}).get("val")) or {}
        totals = token_usage.get("totals") or {}
        if not totals:
            return None

        input_tokens = int(totals.get("uncachedInputTokens") or 0)
        output_tokens = int(totals.get("outputTokens") or 0)
        cache_read = int(totals.get("cacheReadTokens") or 0)
        cache_write = int(totals.get("cacheWriteTokens") or 0)
        if input_tokens == 0 and output_tokens == 0 and cache_read == 0 and cache_write == 0:
            return None

        identity = entry.get("identity") or {}
        cwd = identity.get("cwd") or ""
        project = Path(cwd).name if cwd else ""

        created_ms = identity.get("createdAt")
        ts = datetime.now()
        if created_ms:
            try:
                ts = datetime.fromtimestamp(float(created_ms) / 1000)
            except Exception:
                pass

        model = self._model_for_session(session_id) or "deepseek"

        return UsageRecord(
            agent=self.name,
            model=model,
            timestamp=ts,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read=cache_read,
            cache_write=cache_write,
            cost_usd=0.0,
            session_id=str(session_id),
            project=project,
        )

    def _model_for_session(self, session_id: str) -> str:
        """Best-effort: read model from the session's request/context event in the zstd log."""
        if not self.sessions_dir.exists():
            return ""
        for project_dir in self.sessions_dir.iterdir():
            if not project_dir.is_dir():
                continue
            session_path = project_dir / session_id / "session.jsonl.zstd"
            if not session_path.exists():
                session_path = project_dir / session_id / "session.jsonl"
            if not session_path.exists():
                continue
            try:
                return self._read_model_from_log(session_path)
            except Exception:
                return ""
        return ""

    @staticmethod
    def _read_model_from_log(path: Path) -> str:
        raw = path.read_bytes()
        if path.suffix == ".zstd" or raw[:4] == b"\x28\xb5\x2f\xfd":
            try:
                import io
                import zstandard
            except ImportError:
                return ""
            # Concatenated zstd frames: stream_reader decodes all; decompress() only first frame.
            raw = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(raw)).read()

        text = raw.decode("utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") != "request/context":
                continue
            data = obj.get("data") or {}
            model = data.get("model")
            if model:
                return str(model)
        return ""
