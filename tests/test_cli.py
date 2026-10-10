"""Check CLI argument forwarding and displayed output without live research."""

import sys
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

from research_agent import cli


class CliTests(unittest.TestCase):
    """Check optional output paths, briefing display, and parser-only exits."""

    def invoke(self, argv):
        """Run the CLI against a fake research module and capture its output."""
        fake_agent = ModuleType("research_agent.agent")
        fake_agent.research = Mock(
            return_value={"request": {}, "price": None, "news": []}
        )
        with (
            patch.dict(sys.modules, {"research_agent.agent": fake_agent}),
            patch.object(sys, "argv", argv),
            patch.object(cli, "format_briefing", return_value="briefing"),
            patch("builtins.print") as output,
        ):
            cli.main()
        return fake_agent.research, output

    def test_output_omitted(self):
        research, output = self.invoke(["research-agent", "question"])
        research.assert_called_once_with("question", result_path=None)
        output.assert_any_call("evidence:")
        output.assert_any_call("\nbriefing")

    def test_output_path_with_spaces(self):
        research, _ = self.invoke(
            ["research-agent", "question", "--output", "briefing demo.json"]
        )
        research.assert_called_once_with(
            "question", result_path=Path("briefing demo.json")
        )

    def test_help_does_not_run_research(self):
        fake_agent = ModuleType("research_agent.agent")
        fake_agent.research = Mock()
        with (
            patch.dict(sys.modules, {"research_agent.agent": fake_agent}),
            patch.object(sys, "argv", ["research-agent", "--help"]),
            patch("sys.stdout"),
        ):
            with self.assertRaises(SystemExit) as error:
                cli.main()
        self.assertEqual(error.exception.code, 0)
        fake_agent.research.assert_not_called()

    def test_missing_question_is_rejected(self):
        with (
            patch.object(sys, "argv", ["research-agent"]),
            patch("sys.stderr"),
        ):
            with self.assertRaises(SystemExit) as error:
                cli.main()
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
