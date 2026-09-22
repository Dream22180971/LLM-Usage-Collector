from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from collectors.base import AgentSummary, UsageRecord


class Aggregator:
    """Aggregate UsageRecords by agent, model, date."""

    def __init__(self, records: List[UsageRecord]):
        self.records = records

    def by_agent(self) -> Dict[str, AgentSummary]:
        groups = defaultdict(lambda: AgentSummary(agent=""))
        for r in self.records:
            g = groups[r.agent]
            g.agent = r.agent
            g.total_input += r.input_tokens
            g.total_output += r.output_tokens
            g.total_cache_read += r.cache_read
            g.total_cache_write += r.cache_write
            g.total_cost += r.cost_usd
            g.request_count += 1
            g.session_count = len(set(
                rec.session_id for rec in self.records if rec.agent == r.agent
            ))

            # Track models
            if r.model not in g.models:
                g.models[r.model] = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "count": 0, "cost": 0.0}
            m = g.models[r.model]
            m["input"] += r.input_tokens
            m["output"] += r.output_tokens
            m["cache_read"] += r.cache_read
            m["cache_write"] += r.cache_write
            m["count"] += 1
            m["cost"] += r.cost_usd

            # Track time range
            if g.first_seen is None or r.timestamp < g.first_seen:
                g.first_seen = r.timestamp
            if g.last_seen is None or r.timestamp > g.last_seen:
                g.last_seen = r.timestamp

        return dict(groups)

    def by_model(self) -> Dict[str, dict]:
        groups = defaultdict(lambda: {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "count": 0, "cost": 0.0})
        for r in self.records:
            m = groups[r.model]
            m["input"] += r.input_tokens
            m["output"] += r.output_tokens
            m["cache_read"] += r.cache_read
            m["cache_write"] += r.cache_write
            m["count"] += 1
            m["cost"] += r.cost_usd
        return dict(groups)

    def by_date(self, days: int = 30) -> Dict[str, dict]:
        """Aggregate by date string, last N days."""
        now = datetime.now()
        cutoff = now - timedelta(days=days)
        groups = defaultdict(lambda: {"input": 0, "output": 0, "count": 0, "cost": 0.0})
        for r in self.records:
            ts = r.timestamp.replace(tzinfo=None) if r.timestamp.tzinfo else r.timestamp
            if ts < cutoff:
                continue
            date_key = ts.strftime("%Y-%m-%d")
            d = groups[date_key]
            d["input"] += r.input_tokens
            d["output"] += r.output_tokens
            d["count"] += 1
            d["cost"] += r.cost_usd
        return dict(sorted(groups.items()))

    def by_agent_date(self, days: int = 30) -> Dict[str, Dict[str, dict]]:
        """Aggregate by agent then by date."""
        now = datetime.now()
        cutoff = now - timedelta(days=days)
        groups = defaultdict(lambda: defaultdict(lambda: {"input": 0, "output": 0, "count": 0, "cost": 0.0}))
        for r in self.records:
            ts = r.timestamp.replace(tzinfo=None) if r.timestamp.tzinfo else r.timestamp
            if ts < cutoff:
                continue
            date_key = ts.strftime("%Y-%m-%d")
            d = groups[r.agent][date_key]
            d["input"] += r.input_tokens
            d["output"] += r.output_tokens
            d["count"] += 1
            d["cost"] += r.cost_usd
        return {k: dict(v) for k, v in groups.items()}

    def totals(self) -> dict:
        total_input = sum(r.input_tokens for r in self.records)
        total_output = sum(r.output_tokens for r in self.records)
        total_cache_read = sum(r.cache_read for r in self.records)
        total_cache_write = sum(r.cache_write for r in self.records)
        total_cost = sum(r.cost_usd for r in self.records)
        total_requests = len(self.records)
        unique_sessions = len(set(r.session_id for r in self.records))
        agents = len(set(r.agent for r in self.records))

        first_seen = min((r.timestamp.replace(tzinfo=None) if r.timestamp.tzinfo else r.timestamp for r in self.records), default=None)
        last_seen = max((r.timestamp.replace(tzinfo=None) if r.timestamp.tzinfo else r.timestamp for r in self.records), default=None)

        return {
            "total_input": total_input,
            "total_output": total_output,
            "total_cache_read": total_cache_read,
            "total_cache_write": total_cache_write,
            "total_tokens": total_input + total_output + total_cache_read + total_cache_write,
            "total_cost": total_cost,
            "total_requests": total_requests,
            "unique_sessions": unique_sessions,
            "agents": agents,
            "first_seen": first_seen,
            "last_seen": last_seen,
        }
