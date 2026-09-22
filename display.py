from datetime import datetime
from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich import box

from aggregator import Aggregator
from collectors.base import AgentSummary


console = Console()


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def fmt_cost(c: float) -> str:
    if c == 0:
        return "-"
    if c < 0.01:
        return f"${c:.4f}"
    return f"${c:.2f}"


def display(totals: dict, by_agent: Dict[str, AgentSummary], by_model: dict, by_date: dict):
    """Render the terminal dashboard."""

    # ── Header ──────────────────────────────────────────────
    console.print()
    header = Text()
    header.append("  LLM Usage Dashboard", style="bold white")
    header.append("  |  ", style="dim")
    header.append("Claude Code + Pi + Hermes + OpenCode + ZCode + Codex + MiMo + DSH + Copilot", style="dim")
    console.print(Panel(header, border_style="green", box=box.DOUBLE))

    # ── Overview Cards ──────────────────────────────────────
    cards = []
    cards.append(_card("Total Tokens", fmt_tokens(totals["total_tokens"]), "bold cyan"))
    cards.append(_card("Input / Output", f"{fmt_tokens(totals['total_input'])} / {fmt_tokens(totals['total_output'])}", "white"))
    cards.append(_card("Cache R / W", f"{fmt_tokens(totals['total_cache_read'])} / {fmt_tokens(totals['total_cache_write'])}", "white"))
    cards.append(_card("Total Cost", fmt_cost(totals["total_cost"]), "bold yellow"))
    cards.append(_card("Requests", str(totals["total_requests"]), "bold green"))
    cards.append(_card("Sessions", str(totals["unique_sessions"]), "white"))
    cards.append(_card("Agents", str(totals["agents"]), "white"))

    if totals["first_seen"]:
        span = f"{totals['first_seen'].strftime('%Y-%m-%d')} ~ {totals['last_seen'].strftime('%Y-%m-%d')}"
        cards.append(_card("Time Span", span, "dim"))

    console.print(Columns(cards, equal=True, expand=True))
    console.print()

    # ── Per-Agent Table ─────────────────────────────────────
    agent_table = Table(
        title="By Agent",
        box=box.SIMPLE_HEAVY,
        border_style="green",
        title_style="bold",
        show_lines=True,
        expand=True,
    )
    agent_table.add_column("Agent", style="bold", min_width=18)
    agent_table.add_column("Tokens", justify="right")
    agent_table.add_column("Input", justify="right", style="cyan")
    agent_table.add_column("Output", justify="right", style="magenta")
    agent_table.add_column("Cache R", justify="right", style="dim")
    agent_table.add_column("Cache W", justify="right", style="dim")
    agent_table.add_column("Cost", justify="right", style="yellow")
    agent_table.add_column("Reqs", justify="right")
    agent_table.add_column("Sessions", justify="right")
    agent_table.add_column("Last Active", justify="right", style="dim")

    for name, s in sorted(by_agent.items(), key=lambda x: x[1].total_tokens, reverse=True):
        last = s.last_seen.strftime("%m-%d %H:%M") if s.last_seen else "-"
        agent_table.add_row(
            name,
            fmt_tokens(s.total_tokens),
            fmt_tokens(s.total_input),
            fmt_tokens(s.total_output),
            fmt_tokens(s.total_cache_read),
            fmt_tokens(s.total_cache_write),
            fmt_cost(s.total_cost),
            str(s.request_count),
            str(s.session_count),
            last,
        )
    console.print(agent_table)
    console.print()

    # ── Per-Model Table ─────────────────────────────────────
    model_table = Table(
        title="By Model (Top 15)",
        box=box.SIMPLE_HEAVY,
        border_style="green",
        title_style="bold",
        show_lines=True,
        expand=True,
    )
    model_table.add_column("Model", style="bold", min_width=20)
    model_table.add_column("Tokens", justify="right")
    model_table.add_column("Input", justify="right", style="cyan")
    model_table.add_column("Output", justify="right", style="magenta")
    model_table.add_column("Cost", justify="right", style="yellow")
    model_table.add_column("Reqs", justify="right")

    sorted_models = sorted(by_model.items(), key=lambda x: x[1]["input"] + x[1]["output"], reverse=True)[:15]
    for model_name, m in sorted_models:
        total = m["input"] + m["output"] + m["cache_read"] + m["cache_write"]
        model_table.add_row(
            model_name,
            fmt_tokens(total),
            fmt_tokens(m["input"]),
            fmt_tokens(m["output"]),
            fmt_cost(m["cost"]),
            str(m["count"]),
        )
    console.print(model_table)
    console.print()

    # ── Daily Trend (last 14 days) ─────────────────────────
    recent_dates = dict(list(by_date.items())[-14:])
    if recent_dates:
        daily_table = Table(
            title="Daily Trend (last 14 days)",
            box=box.SIMPLE_HEAVY,
            border_style="green",
            title_style="bold",
            expand=True,
        )
        daily_table.add_column("Date", style="dim", min_width=12)
        daily_table.add_column("Tokens", justify="right")
        daily_table.add_column("Input", justify="right", style="cyan")
        daily_table.add_column("Output", justify="right", style="magenta")
        daily_table.add_column("Cost", justify="right", style="yellow")
        daily_table.add_column("Reqs", justify="right")
        daily_table.add_column("Bar", min_width=20)

        max_tokens = max(
            (d["input"] + d["output"] for d in recent_dates.values()),
            default=1,
        )

        for date_str, d in recent_dates.items():
            t = d["input"] + d["output"]
            bar_len = int(t / max_tokens * 20) if max_tokens > 0 else 0
            bar = "█" * bar_len + "░" * (20 - bar_len)
            daily_table.add_row(
                date_str,
                fmt_tokens(t),
                fmt_tokens(d["input"]),
                fmt_tokens(d["output"]),
                fmt_cost(d["cost"]),
                str(d["count"]),
                bar,
            )
        console.print(daily_table)
        console.print()

    # ── Footer ──────────────────────────────────────────────
    console.print(
        f"  [dim]Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
        justify="right",
    )
    console.print()


def _card(label: str, value: str, style: str) -> Panel:
    text = Text()
    text.append(value, style=style)
    text.append(f"\n{label}", style="dim")
    return Panel(text, border_style="dim", box=box.ROUNDED, padding=(0, 1))
