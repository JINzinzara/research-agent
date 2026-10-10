"""Check the research cutoff and period-first RSS selection without API calls."""

import os
import unittest
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from io import BytesIO
from unittest.mock import patch
from xml.etree import ElementTree as ET

with (
    patch.dict(os.environ, {"COINGECKO_API_KEY": "offline-fixture"}),
    patch("openai.OpenAI"),
    patch("coingecko_sdk.Coingecko"),
):
    from research_agent import agent


class NewsWindowTests(unittest.TestCase):
    """Check cutoff boundaries, article priority, and the five-item limit."""

    def setUp(self):
        self.reference = datetime(2026, 10, 10, 12, tzinfo=timezone.utc)
        self.start, self.end = agent.research_news_window(self.reference)

    def fetch(self, dates):
        """Read a synthetic RSS feed with one matching item per supplied date."""
        root = ET.Element("rss")
        channel = ET.SubElement(root, "channel")
        for index, date in enumerate(dates):
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = f"Bitcoin article {index}"
            ET.SubElement(item, "link").text = f"https://example.com/{index}"
            if date is not None:
                ET.SubElement(item, "pubDate").text = format_datetime(date)
        with patch.object(
            agent, "urlopen", return_value=BytesIO(ET.tostring(root))
        ) as fetch:
            result = agent.get_news("Bitcoin", self.start, self.end)
        self.assertEqual(fetch.call_args.kwargs["timeout"], 10)
        return result

    def test_end_is_reference_not_midnight(self):
        self.assertEqual(self.start.isoformat(), "2026-10-08T15:00:00+00:00")
        self.assertEqual(self.end, self.reference)
        self.assertEqual(self.end - self.start, timedelta(hours=45))

    def test_kst_input_returns_utc_bounds(self):
        kst_reference = self.reference.astimezone(timezone(timedelta(hours=9)))
        self.assertEqual(
            agent.research_news_window(kst_reference), (self.start, self.end)
        )

    def test_naive_reference_is_rejected(self):
        with self.assertRaises(ValueError):
            agent.research_news_window(datetime(2026, 10, 10))

    def test_start_included_end_excluded(self):
        self.assertEqual(
            agent.classify_news_period(self.start.isoformat(), self.start, self.end),
            "in_period",
        )
        self.assertEqual(
            agent.classify_news_period(self.end.isoformat(), self.start, self.end),
            "outside_period",
        )

    def test_scan_past_first_five_to_prioritize_in_period(self):
        old = self.start - timedelta(seconds=1)
        result = self.fetch([old] * 5 + [self.start, self.end - timedelta(seconds=1)])
        self.assertEqual(len(result), 5)
        self.assertEqual([article["title"] for article in result[:2]],
                         ["Bitcoin article 5", "Bitcoin article 6"])

    def test_five_not_three_in_period_articles(self):
        result = self.fetch([self.start] * 7)
        self.assertEqual(len(result), 5)
        self.assertTrue(all(
            agent.classify_news_period(article["published_at"], self.start, self.end)
            == "in_period" for article in result
        ))

    def test_unknown_and_outside_articles_remain_references(self):
        result = self.fetch([None, self.end, self.start])
        self.assertEqual([article["title"] for article in result],
                         ["Bitcoin article 2", "Bitcoin article 1", "Bitcoin article 0"])
        self.assertIsNone(result[-1]["published_at"])


if __name__ == "__main__":
    unittest.main()
