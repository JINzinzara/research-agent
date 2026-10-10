"""Normalize timestamps and classify articles against an explicit news window"""

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

KST = timezone(timedelta(hours=9))


def to_utc_iso(value):
    """Convert Unix seconds or an RSS date to UTC ISO 8601, preserving missing times"""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        timestamp = datetime.fromtimestamp(value, timezone.utc)
    elif isinstance(value, str):
        timestamp = parsedate_to_datetime(value)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
    else:
        raise TypeError("timestamp must be a number, string or None")
    return timestamp.astimezone(timezone.utc).isoformat()


def research_news_window(reference_at):
    """Return UTC bounds from previous KST midnight to the fixed research start"""
    if reference_at.tzinfo is None or reference_at.utcoffset() is None:
        raise ValueError("reference_at must include timezone information")
    today_midnight = reference_at.astimezone(KST).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start = today_midnight - timedelta(days=1)
    return start.astimezone(timezone.utc), reference_at.astimezone(timezone.utc)


def classify_news_period(published_at, start, end):
    """Classify a UTC ISO publication time using inclusive start and exclusive end"""
    if published_at is None:
        return "unknown"
    published = datetime.fromisoformat(published_at)
    return "in_period" if start <= published < end else "outside_period"


def group_news_by_period(news, start, end):
    """Group articles by publication time without changing their content or sources"""
    groups = {"in_period": [], "outside_period": [], "unknown": []}
    for article in news:
        period = classify_news_period(article.get("published_at"), start, end)
        groups[period].append(article)
    return groups
