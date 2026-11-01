
import json
from datetime import UTC, datetime
from pathlib import Path

LOG_FILE = Path(__file__).resolve().parent.parent / "data" / "usage.jsonl"


def log_usage(model, input_tokens, output_tokens, input_rate, output_rate):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    total_tokens = input_tokens + output_tokens

    estimated_cost = (
        input_tokens * input_rate
        + output_tokens * output_rate
    ) / 1_000_000

    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": round(estimated_cost, 8),
    }

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")

    return record


def get_usage_summary():
    if not LOG_FILE.exists():
        return {
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0,
        }

    records = []

    with LOG_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    return {
        "total_requests": len(records),
        "total_input_tokens": sum(r["input_tokens"] for r in records),
        "total_output_tokens": sum(r["output_tokens"] for r in records),
        "total_tokens": sum(r["total_tokens"] for r in records),
        "estimated_cost": round(
            sum(r["estimated_cost"] for r in records), 8
        ),
        "currency": "USD",
    }
