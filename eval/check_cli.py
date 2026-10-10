import sys
from types import ModuleType
from unittest.mock import Mock, patch
from pathlib import Path

from research_agent.cli import main


def check_output_omitted():
    fake_agent = ModuleType("research_agent.agent")
    fake_agent.research = Mock()

    with patch.dict(sys.modules, {"research_agent.agent": fake_agent}):
        with patch.object(sys, "argv", ["research-agent", "question"]):
            main()

    fake_agent.research.assert_called_once_with("question", result_path=None)


def check_output_provided():
    fake_agent = ModuleType("research_agent.agent")
    fake_agent.research = Mock()

    output_path = "briefing demo.json"

    argv = [
        "research-agent",
        "question",
        "--output",
        output_path,
    ]

    with patch.dict(sys.modules, {"research_agent.agent": fake_agent}):
        with patch.object(sys, "argv", argv):
            main()

    fake_agent.research.assert_called_once_with(
        "question", result_path=Path(output_path)
    )


if __name__ == "__main__":
    check_output_omitted()
    check_output_provided()
