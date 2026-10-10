"""Coordinate evidence collection, grounded synthesis, and optional result storage."""

from datetime import datetime, timezone

from research_agent.briefing import format_sources, save_result
from research_agent.collectors import get_news, get_price
from research_agent.generation import extract_request, synthesize
from research_agent.periods import group_news_by_period, research_news_window


def research(question, result_path=None):
    """Return a complete research result and optionally save it without overwriting."""
    reference_at = datetime.now(timezone.utc)
    start, end = research_news_window(reference_at)
    news_window = {"start": start.isoformat(), "end": end.isoformat()}
    request_info = extract_request(question)
    warnings = []

    try:
        price = get_price(request_info["coin_id"], request_info["currency"])
    except Exception as error:
        price = None
        warnings.append(f"Price collection failed: {type(error).__name__}")

    news_failed = False
    try:
        news = get_news(request_info["news_query"], start, end)
    except Exception as error:
        news = []
        news_failed = True
        warnings.append(f"News collection failed: {type(error).__name__}")

    if not news and not news_failed:
        warnings.append("No matching news found in the current RSS feed")

    if price is not None:
        if price.get("change_24h_pct") is None:
            warnings.append("24-hour price change is unavailable")
        if price.get("last_updated_at") is None:
            warnings.append("Price update time is unavailable")

    for index, article in enumerate(news, start=1):
        if article.get("published_at") is None:
            warnings.append(f"News publication time is unavailable: article {index}")

    news_groups = group_news_by_period(news, start, end)
    if news and not news_groups["in_period"]:
        warnings.append(
            "No news within the requested window found in the collected RSS evidence"
        )

    if price is None and not news:
        answer = (
            "수집된 근거가 없어 답변을 생성하지 않았습니다. /"
            "No evidence was collected, so no answer was generated"
        )
        status = "failed"
    else:
        answer = synthesize(question, request_info, price, news_window, news_groups)
        status = "partial" if warnings else "ok"

    result = {
        "request": request_info,
        "price": price,
        "news": news,
        "answer": answer,
        "sources": format_sources(price, news),
        "status": status,
        "warnings": warnings,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "news_window": news_window,
        "news_groups": news_groups,
    }
    if result_path is not None:
        save_result(result, result_path)
    return result
