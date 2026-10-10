"""Check the research pipeline, saved results, and existing fixture evaluations."""

import json
import unittest
from datetime import datetime, timedelta, timezone
from functools import partial
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from eval.run_eval import CASES_PATH, load_cases, run_case
from research_agent import agent


class AgentTests(unittest.TestCase):
    """Check orchestration with mocked collectors and model functions."""

    def test_cutoff_stays_fixed_across_midnight_and_result_is_saved(self):
        reference = datetime(2026, 10, 8, 14, 59, 59, tzinfo=timezone.utc)
        completed = reference + timedelta(seconds=2)
        request = {"coin_id": "bitcoin", "currency": "usd", "news_query": "Bitcoin"}
        price = {
            "price": 100,
            "change_24h_pct": 5,
            "last_updated_at": reference.isoformat(),
            "source_url": "https://example.com/price",
        }
        news = [
            {
                "title": "Bitcoin before cutoff",
                "source_url": "https://example.com/in",
                "published_at": (reference - timedelta(seconds=1)).isoformat(),
            },
            {
                "title": "Bitcoin at cutoff",
                "source_url": "https://example.com/out",
                "published_at": reference.isoformat(),
            },
            {
                "title": "Bitcoin unknown",
                "source_url": "https://example.com/unknown",
                "published_at": None,
            },
        ]
        with TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            with (
                patch.object(agent, "datetime", wraps=datetime) as clock,
                patch.object(agent, "extract_request", return_value=request),
                patch.object(agent, "get_price", return_value=price),
                patch.object(agent, "get_news", return_value=news) as fetch_news,
                patch.object(
                    agent, "synthesize", return_value="테스트 답변"
                ) as synthesize,
                patch("builtins.print") as print_output,
            ):
                clock.now.side_effect = [reference, completed]
                result = agent.research("Bitcoin", result_path=output)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), result)
        self.assertEqual(
            result["news_window"],
            {
                "start": "2026-10-06T15:00:00+00:00",
                "end": reference.isoformat(),
            },
        )
        self.assertEqual(result["collected_at"], completed.isoformat())
        self.assertEqual(
            result["news_groups"],
            {
                "in_period": [news[0]],
                "outside_period": [news[1]],
                "unknown": [news[2]],
            },
        )
        self.assertEqual(result["status"], "partial")
        self.assertEqual(
            result["warnings"], ["News publication time is unavailable: article 3"]
        )
        fetch_news.assert_called_once_with(
            "Bitcoin", datetime(2026, 10, 6, 15, tzinfo=timezone.utc), reference
        )
        synthesize.assert_called_once_with(
            "Bitcoin", request, price, result["news_window"], result["news_groups"]
        )
        print_output.assert_not_called()
        for article in news:
            self.assertIn(article["source_url"], result["sources"])

    def test_planner_failure_stops_collection(self):
        with (
            patch.object(
                agent, "extract_request", side_effect=ValueError("invalid plan")
            ),
            patch.object(agent, "get_price") as price,
            patch.object(agent, "get_news") as news,
        ):
            with self.assertRaises(ValueError):
                agent.research("Bitcoin")
        price.assert_not_called()
        news.assert_not_called()


def load_tests(loader, tests, pattern):
    """Include all existing JSONL evaluations in the standard unittest command."""
    for case in load_cases(CASES_PATH):
        fixture_check = partial(run_case, case)
        fixture_check.__name__ = case["id"]
        tests.addTest(unittest.FunctionTestCase(fixture_check, description=case["id"]))
    return tests


if __name__ == "__main__":
    unittest.main()
