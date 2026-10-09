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
