"""Check source rendering, UTF-8 storage, and offline replay."""

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from research_agent import briefing


class BriefingTests(unittest.TestCase):
    """Check formatting and storage without provider dependencies."""

    def setUp(self):
        self.result = {
            "status": "partial",
            "news_window": {
                "start": "2026-10-08T15:00:00+00:00",
                "end": "2026-10-10T12:00:00+00:00",
            },
            "collected_at": "2026-10-10T12:01:00+00:00",
            "warnings": ["Price update time is unavailable"],
            "answer": "테스트 답변",
            "sources": "Sources:\n- No sources collected",
        }

    def test_sources_preserve_links_when_times_are_missing(self):
        price = {"source_url": "https://example.com/price"}
        for article in [
            {"source_url": "https://example.com/news", "published_at": None},
            {"source_url": "https://example.com/news"},
        ]:
            with self.subTest(article=article):
                self.assertEqual(
                    briefing.format_sources(price, [article]),
                    "Sources:\n- [CoinGecko price](https://example.com/price)\n"
                    "- [CoinDesk news 1](https://example.com/news) - Published: Unknown",
                )
        self.assertEqual(
            briefing.format_sources(None, []), "Sources:\n- No sources collected"
        )
        self.assertEqual(
            briefing.format_sources(price, []),
            "Sources:\n- [CoinGecko price](https://example.com/price)",
        )

    def test_rendered_window_generation_time_warnings_and_sources(self):
        original = deepcopy(self.result)
        text = briefing.format_briefing(self.result)
        self.assertEqual(
            text,
            "Status: partial\n"
            "News window (KST): [2026-10-09T00:00:00+09:00, 2026-10-10T21:00:00+09:00)\n"
            "Generated at (KST): 2026-10-10T21:01:00+09:00\n\n"
            "Warnings:\n- Price update time is unavailable\n\n"
            "테스트 답변\n\nSources:\n- No sources collected",
        )
        self.assertEqual(self.result, original)

    def test_ok_and_failed_status_rendering(self):
        ok = {**self.result, "status": "ok", "warnings": []}
        self.assertIn("Warnings:\n- No warnings", briefing.format_briefing(ok))
        failed = {
            **self.result,
            "status": "failed",
            "warnings": ["Price collection failed: RuntimeError"],
            "answer": "수집된 근거가 없어 답변을 생성하지 않았습니다.",
        }
        text = briefing.format_briefing(failed)
        self.assertTrue(text.startswith("Status: failed\n"))
        self.assertTrue(text.endswith(failed["answer"] + "\n\n" + failed["sources"]))

    def test_json_round_trip_and_overwrite_protection(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "briefing demo.json"
            briefing.save_result(self.result, output)
            original = output.read_bytes()
            self.assertEqual(json.loads(original.decode("utf-8")), self.result)
            self.assertIn("테스트 답변", original.decode("utf-8"))
            with self.assertRaises(FileExistsError):
                briefing.save_result({**self.result, "answer": "changed"}, output)
            self.assertEqual(output.read_bytes(), original)

    def test_non_dict_results_are_rejected(self):
        with self.assertRaises(TypeError):
            briefing.save_result([], "unused.json")

    def test_replay_main_prints_saved_result(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "result.json"
            briefing.save_result(self.result, output)
            with (
                patch.object(sys, "argv", ["briefing", str(output)]),
                patch("builtins.print") as print_result,
            ):
                briefing.main()
        print_result.assert_called_once_with(briefing.format_briefing(self.result))

    def test_replay_rejects_non_object_json(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "array.json"
            with output.open("x", encoding="utf-8") as file:
                json.dump([], file)
            with patch.object(sys, "argv", ["briefing", str(output)]):
                with self.assertRaises(ValueError):
                    briefing.main()


if __name__ == "__main__":
    unittest.main()
