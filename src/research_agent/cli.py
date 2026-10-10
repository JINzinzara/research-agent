"""Run live research and display its evidence and briefing."""

import argparse
import json
from pathlib import Path

from research_agent.briefing import format_briefing


def main():
    """Parse a question and optional output path, then run and display research."""
    parser = argparse.ArgumentParser(
        description="Run research and optionally save its result"
    )
    parser.add_argument("question")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    from research_agent.agent import research

    result = research(args.question, result_path=args.output)
    print("evidence:")
    print(
        json.dumps(
            {key: result[key] for key in ("request", "price", "news")},
            ensure_ascii=False,
            indent=2,
        )
    )
    print("\n" + format_briefing(result))


if __name__ == "__main__":
    main()
