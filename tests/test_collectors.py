"""Check provider parsing and authentication setup without fetching market data."""

import os
import unittest
from datetime import datetime, timezone
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from research_agent import collectors


class CollectorTests(unittest.TestCase):
    """Check price fields, RSS matching, and retained provider configuration."""

    def price(self, row):
        """Return a parsed price using a fake SDK response."""
        client = Mock()
        client.simple.price.get.return_value = {
            "bitcoin": SimpleNamespace(to_dict=lambda: row)
        }
        with patch.object(collectors, "_price_client", return_value=client):
            result = collectors.get_price("bitcoin", "usd")
        client.simple.price.get.assert_called_once_with(
            ids="bitcoin",
            vs_currencies="usd",
            include_24hr_change=True,
            include_last_updated_at=True,
        )
        return result

    def test_price_fields_and_source(self):
        result = self.price({"usd": 100, "usd_24h_change": 5, "last_updated_at": 0})
        self.assertEqual(result["price"], 100)
        self.assertEqual(result["change_24h_pct"], 5)
        self.assertEqual(result["last_updated_at"], "1970-01-01T00:00:00+00:00")
        self.assertEqual(
            result["source_url"],
            "https://api.coingecko.com/api/v3/simple/price?"
            "vs_currencies=usd&ids=bitcoin"
            "&include_24hr_change=true&include_last_updated_at=true",
        )

    def test_missing_optional_price_fields_remain_none(self):
        result = self.price({"usd": 100})
        self.assertIsNone(result["change_24h_pct"])
        self.assertIsNone(result["last_updated_at"])

    def test_missing_price_is_rejected(self):
        with self.assertRaises(ValueError):
            self.price({"usd_24h_change": 5})

    def test_demo_client_configuration_and_cache(self):
        collectors._price_client.cache_clear()
        try:
            with (
                patch.dict(os.environ, {"COINGECKO_API_KEY": "test-fixture"}),
                patch("coingecko_sdk.Coingecko") as constructor,
            ):
                first = collectors._price_client()
                self.assertIs(first, collectors._price_client())
                constructor.assert_called_once_with(
                    demo_api_key="test-fixture",
                    environment="demo",
                    timeout=10,
                    max_retries=0,
                )
        finally:
            collectors._price_client.cache_clear()

    def test_rss_matching_and_missing_fields(self):
        feed = b"""<rss><channel>
          <item><title>Other asset</title><link>https://example.com/other</link></item>
          <item><title>Market note</title><description>BITCOIN research</description>
            <link>https://example.com/matched</link></item>
          <item><title>Bitcoin without link</title></item>
          <item><link>https://example.com/no-title</link></item>
        </channel></rss>"""
        start = datetime(2026, 10, 9, tzinfo=timezone.utc)
        end = datetime(2026, 10, 10, tzinfo=timezone.utc)
        with patch.object(collectors, "urlopen", return_value=BytesIO(feed)):
            result = collectors.get_news("Bitcoin", start, end)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["source_url"], "https://example.com/matched")
        self.assertIsNone(result[0]["published_at"])


if __name__ == "__main__":
    unittest.main()
