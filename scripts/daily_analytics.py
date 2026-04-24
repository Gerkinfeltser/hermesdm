#!/usr/bin/env python3
"""
scripts/daily_analytics.py — Genera reporte diario de uso de HermesDM.

Lee los audit logs JSONL de las últimas 24h y produce métricas:
  - Comandos ejecutados y distribución
  - LLM calls, tokens consumidos, latencia promedio
  - Errores y tasa de error
  - Usuarios más activos
  - Modelos usados

Uso:
    python scripts/daily_analytics.py
    python scripts/daily_analytics.py --hours 48
    python scripts/daily_analytics.py --output /tmp/report.md
    python scripts/daily_analytics.py --telegram "telegram:-1003916745496"
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.audit_logger import AuditLogger


def parse_timestamp(ts: str) -> datetime:
    """Parse ISO timestamp string to datetime."""
    # Handle Z suffix and +00:00
    ts = ts.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return datetime.now(timezone.utc)


def load_events(hours: int = 24) -> list[dict[str, Any]]:
    """Load all audit events from the last N hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    files = AuditLogger._list_audit_files()
    events: list[dict[str, Any]] = []

    for fpath in reversed(files):
        with open(fpath, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ts_str = event.get("timestamp", "")
                if ts_str:
                    try:
                        ts = parse_timestamp(ts_str)
                        if ts < cutoff:
                            continue
                    except Exception:
                        pass

                events.append(event)

    return events


def compute_metrics(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate metrics from a list of events."""
    commands_received = [e for e in events if e.get("event_type") == "command_received"]
    commands_executed = [e for e in events if e.get("event_type") == "command_executed"]
    llm_calls = [e for e in events if e.get("event_type") == "llm_call"]
    errors = [e for e in events if e.get("event_type") == "error"]

    # Command distribution
    cmd_counter: Counter[str] = Counter()
    for e in commands_received:
        handler = (e.get("metadata") or {}).get("handler", "unknown")
        cmd_counter[handler] += 1

    # User activity
    user_counter: Counter[str] = Counter()
    for e in commands_received:
        user = e.get("username") or str(e.get("user_id", "unknown"))
        # Skip test/mock usernames
        if "MagicMock" in user or "mock" in user.lower():
            continue
        user_counter[user] += 1

    # LLM metrics
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    latencies: list[float] = []
    model_counter: Counter[str] = Counter()
    error_count = len(errors)

    for e in llm_calls:
        meta = e.get("metadata") or {}
        usage = meta.get("usage") or {}

        if usage:
            total_prompt_tokens += usage.get("prompt_tokens", 0)
            total_completion_tokens += usage.get("completion_tokens", 0)
            total_tokens += usage.get("total_tokens", 0)

        latency = meta.get("latency_ms")
        if latency is not None:
            latencies.append(latency)

        model = meta.get("model", "unknown")
        model_counter[model] += 1

    # Error rate (relative to commands)
    cmd_count = len(commands_received)
    error_rate = (error_count / cmd_count * 100) if cmd_count > 0 else 0.0

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    max_latency = max(latencies) if latencies else 0.0
    min_latency = min(latencies) if latencies else 0.0

    return {
        "period_hours": None,  # filled by caller
        "total_events": len(events),
        "commands_received": len(commands_received),
        "commands_executed": len(commands_executed),
        "llm_calls": len(llm_calls),
        "error_count": error_count,
        "error_rate_percent": round(error_rate, 2),
        "command_distribution": dict(cmd_counter.most_common(15)),
        "user_activity": dict(user_counter.most_common(10)),
        "tokens": {
            "prompt": total_prompt_tokens,
            "completion": total_completion_tokens,
            "total": total_tokens,
        },
        "latency_ms": {
            "avg": round(avg_latency, 2),
            "min": round(min_latency, 2),
            "max": round(max_latency, 2),
        },
        "models_used": dict(model_counter),
    }


def format_report(metrics: dict[str, Any], hours: int) -> str:
    """Format metrics as a Telegram-friendly markdown report."""
    lines: list[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines.append(f"📊 *HermesDM Analytics* — últimas {hours}h")
    lines.append(f"🕒 {now}\n")

    lines.append("*Resumen*")
    lines.append(f"• Comandos: {metrics['commands_received']}")
    lines.append(f"• LLM calls: {metrics['llm_calls']}")
    lines.append(f"• Errores: {metrics['error_count']} ({metrics['error_rate_percent']}%)")
    lines.append("")

    lines.append("*Tokens consumidos*")
    tok = metrics["tokens"]
    lines.append(f"• Prompt: {tok['prompt']:,}")
    lines.append(f"• Completion: {tok['completion']:,}")
    lines.append(f"• Total: {tok['total']:,}")
    lines.append("")

    lines.append("*Latencia LLM*")
    lat = metrics["latency_ms"]
    lines.append(f"• Promedio: {lat['avg']} ms")
    lines.append(f"• Mín: {lat['min']} ms | Máx: {lat['max']} ms")
    lines.append("")

    if metrics["models_used"]:
        lines.append("*Modelos*")
        for model, count in metrics["models_used"].items():
            lines.append(f"• {model}: {count} calls")
        lines.append("")

    if metrics["command_distribution"]:
        lines.append("*Comandos más usados*")
        for cmd, count in list(metrics["command_distribution"].items())[:10]:
            lines.append(f"• /{cmd}: {count}")
        lines.append("")

    if metrics["user_activity"]:
        lines.append("*Usuarios más activos*")
        for user, count in metrics["user_activity"].items():
            lines.append(f"• {user}: {count} cmds")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="HermesDM Daily Analytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--hours", "-H", type=int, default=24,
        help="Hours to look back (default: 24)"
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Write report to file path"
    )
    parser.add_argument(
        "--json", "-j", action="store_true",
        help="Output raw JSON metrics instead of markdown"
    )
    parser.add_argument(
        "--telegram", "-t", type=str, default=None,
        help="Send report to Telegram target, e.g. telegram:-1003916745496"
    )

    args = parser.parse_args()

    events = load_events(hours=args.hours)
    metrics = compute_metrics(events)
    metrics["period_hours"] = args.hours

    if args.json:
        report = json.dumps(metrics, indent=2, ensure_ascii=False)
    else:
        report = format_report(metrics, args.hours)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)

    if args.telegram:
        try:
            from hermes_tools import send_message
            send_message(message=report, target=args.telegram)
            print(f"Report sent to {args.telegram}")
        except Exception as exc:
            print(f"Failed to send Telegram message: {exc}")


if __name__ == "__main__":
    main()
