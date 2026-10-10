"""Collect CoinGecko Demo prices and period-prioritized CoinDesk RSS articles"""

import os
from functools import lru_cache
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from research_agent.periods import group_news_by_period, to_utc_iso

RSS_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/"
MAX_NEWS_ITEMS = 5


@lru_cache(maxsize=1)
def _price_client():
    """Create the Demo client only when a price request needs authentication"""
    from coingecko_sdk import Coingecko

    return Coingecko(
        demo_api_key=os.environ["COINGECKO_API_KEY"],
        environment="demo",
        timeout=10,
        max_retries=0,
    )


def get_price(coin_id, currency):
    """Fetch a quoted price, rolling 24-hour change, update time, and source URL"""
    response = _price_client().simple.price.get(
        ids=coin_id,
        vs_currencies=currency,
        include_24hr_change=True,
        include_last_updated_at=True,
    )
    row = response[coin_id].to_dict()
    price = row.get(currency)
    if price is None:
        raise ValueError("CoinGecko response is missing price")
    return {
        "price": price,
        "change_24h_pct": row.get(f"{currency}_24h_change"),
        "last_updated_at": to_utc_iso(row.get("last_updated_at")),
        "source_url": (
            "https://api.coingecko.com/api/v3/simple/price?"
            f"vs_currencies={currency}&ids={coin_id}"
            "&include_24hr_change=true&include_last_updated_at=true"
        ),
    }


def get_news(news_query, start, end):
    """Fetch up to five matching RSS articles, prioritizing the requested window"""
    request = Request(RSS_URL, headers={"User-Agent": "research-agent/0.1"})
    with urlopen(request, timeout=10) as response:
        root = ET.fromstring(response.read())

    articles = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        summary = item.findtext("description") or ""
        source_url = (item.findtext("link") or "").strip()
        if not title or not source_url:
            continue
        if news_query.casefold() not in f"{title} {summary}".casefold():
            continue
        articles.append(
            {
                "title": title,
                "summary": summary,
                "source_url": source_url,
                "published_at": to_utc_iso(item.findtext("pubDate")),
            }
        )

    # shortcut: the current RSS feed is not a full archive; persist articles for coverage.
    groups = group_news_by_period(articles, start, end)
    selected = groups["in_period"] + groups["outside_period"] + groups["unknown"]
    return selected[:MAX_NEWS_ITEMS]
