"""Format research evidence and briefings, save JSON, and replay saved results."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from research_agent.periods import KST


def format_sources(price, news):
    """Format source URLs with publication times, keeping links when times are missing."""
    sources = []
    if price is not None:
        sources.append(f"- [CoinGecko price]({price['source_url']})")
    for index, article in enumerate(news, start=1):
        published_at = article.get("published_at") or "Unknown"
        sources.append(
            f"- [CoinDesk news {index}]({article['source_url']})"
            f" - Published: {published_at}"
        )
    return "Sources:\n" + ("\n".join(sources) if sources else "- No sources collected")


def format_briefing(result):
    """Render status, KST window, generation time, warnings, answer, and sources."""
    start_kst = datetime.fromisoformat(result["news_window"]["start"]).astimezone(KST)
    end_kst = datetime.fromisoformat(result["news_window"]["end"]).astimezone(KST)
    generated_kst = datetime.fromisoformat(result["collected_at"]).astimezone(KST)
    lines = [
        f"Status: {result['status']}",
        f"News window (KST): [{start_kst.isoformat()}, {end_kst.isoformat()})",
        f"Generated at (KST): {generated_kst.isoformat()}",
        "",
        "Warnings:",
    ]
    lines.extend(f"- {warning}" for warning in result["warnings"])
    if not result["warnings"]:
        lines.append("- No warnings")
    lines.extend(["", result["answer"], "", result["sources"]])
    return "\n".join(lines)


def save_result(result, result_path):
    """Save a result as UTF-8 JSON, rejecting non-dicts and existing files."""
    if not isinstance(result, dict):
        raise TypeError("result must be a dict")
    text = json.dumps(result, ensure_ascii=False, indent=2)
    with Path(result_path).open("x", encoding="utf-8") as file:
        file.write(text + "\n")


def main():
    """Render one saved JSON result without authentication or external calls."""
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
