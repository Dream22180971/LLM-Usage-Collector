from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UsageRecord:
    agent: str
    model: str
    timestamp: datetime
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    cache_write: int = 0
    cost_usd: float = 0.0
    session_id: str = ""
    project: str = ""

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens + self.cache_read + self.cache_write


@dataclass
class AgentSummary:
    agent: str
    total_input: int = 0
    total_output: int = 0
    total_cache_read: int = 0
    total_cache_write: int = 0
    total_cost: float = 0.0
    session_count: int = 0
    request_count: int = 0
    models: dict = field(default_factory=dict)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    @property
    def total_tokens(self) -> int:
        return self.total_input + self.total_output + self.total_cache_read + self.total_cache_write
