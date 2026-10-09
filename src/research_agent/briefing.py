import argparse
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone


def format_briefing(result):
    """Return briefing text with explicit status, timestamps and warnings"""
    kst = timezone(timedelta(hours=9))

    start_kst = datetime.fromisoformat(result["news_window"]["start"]).astimezone(kst)
    end_kst = datetime.fromisoformat(result["news_window"]["end"]).astimezone(kst)
    generated_kst = datetime.fromisoformat(result["collected_at"]).astimezone(kst)

    lines = [
        f"Status: {result['status']}",
        (f"News window (KST): " f"[{start_kst.isoformat()}, {end_kst.isoformat()})"),
        f"Generated at (KST): {generated_kst.isoformat()}",
        "",
        "Warnings:",
    ]

    if result["warnings"]:
        for warning in result["warnings"]:
            lines.append(f"- {warning}")
    else:
        lines.append("- No warnings")

    lines.extend(
        [
            "",
            result["answer"],
            "",
            result["sources"],
        ]
    )

    return "\n".join(lines)


def save_result(result, result_path):
    """Save a complete research result without overwriting an existing file"""
    if not isinstance(result, dict):
        raise TypeError("result must be a dict")
    text = json.dumps(result, ensure_ascii=False, indent=2)
    with Path(result_path).open("x", encoding="utf-8") as file:
        file.write(text + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Render a saved research result without external API calls"
    )
    parser.add_argument("result_path", type=Path)
    args = parser.parse_args()

    result = json.loads(args.result_path.read_text(encoding="utf-8"))

    if not isinstance(result, dict):
        raise ValueError("saved result must be a JSON object")

    print(format_briefing(result))


if __name__ == "__main__":
    main()
