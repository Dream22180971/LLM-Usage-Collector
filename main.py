#!/usr/bin/env python3
"""LLM Usage Collector - Aggregate token usage across Claude Code, Pi Agent, Hermes, OpenCode, ZCode, Codex, MiMo Desktop, DSH, Copilot."""

import sys
import os
import json
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

# Fix Windows GBK encoding for rich
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from collectors import (
    ClaudeCollector,
    PiCollector,
    HermesCollector,
    OpenCodeCollector,
    ZCodeCollector,
    CodexCollector,
    MimoCollector,
    DshCollector,
    CopilotCollector,
)
from aggregator import Aggregator
from display import display, console


def collect_all(quiet: bool = False):
    """Run all collectors and merge results."""
    collectors = [
        ClaudeCollector(),
        PiCollector(),
        HermesCollector(),
        OpenCodeCollector(),
        ZCodeCollector(),
        CodexCollector(),
        MimoCollector(),
        DshCollector(),
        CopilotCollector(),
    ]
    all_records = []
    for c in collectors:
        try:
            records = c.collect()
            all_records.extend(records)
            if not quiet:
                console.print(f"  [green]+[/green] {c.name}: {len(records)} records")
        except Exception as e:
            if not quiet:
                console.print(f"  [red]x[/red] {c.name}: {e}")
    return all_records


def main():
    import argparse
    parser = argparse.ArgumentParser(description="LLM Usage Dashboard")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--agent", type=str, help="Filter by agent name")
    parser.add_argument("--days", type=int, default=30, help="Date range for daily trend (default: 30)")
    args = parser.parse_args()

    if not args.json:
        console.print()
        console.print("  [bold green]Scanning agents...[/bold green]")
        console.print()

    records = collect_all(quiet=args.json)
    if not args.json:
        console.print()

    if not records:
        if not args.json:
            console.print("  [yellow]No usage data found.[/yellow]")
        return

    agg = Aggregator(records)

    if args.agent:
        records = [r for r in records if args.agent.lower() in r.agent.lower()]
        agg = Aggregator(records)

    if args.json:
        totals = agg.totals()
        by_agent = {k: {
            "total_tokens": v.total_tokens,
            "total_input": v.total_input,
            "total_output": v.total_output,
            "total_cache_read": v.total_cache_read,
            "total_cache_write": v.total_cache_write,
            "total_cost": v.total_cost,
            "request_count": v.request_count,
            "session_count": v.session_count,
        } for k, v in agg.by_agent().items()}
        output = {
            "totals": {k: v for k, v in totals.items() if k not in ("first_seen", "last_seen")},
            "by_agent": by_agent,
            "by_model": agg.by_model(),
            "by_date": agg.by_date(args.days),
        }
        print(json.dumps(output, indent=2, default=str))
    else:
        display(
            totals=agg.totals(),
            by_agent=agg.by_agent(),
            by_model=agg.by_model(),
            by_date=agg.by_date(args.days),
        )


if __name__ == "__main__":
    main()
