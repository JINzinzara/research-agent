import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run research and optionally save its result"
    )

    parser.add_argument("question")
    parser.add_argument("--output", type=Path, default=None)

    args = parser.parse_args()

    from research_agent.agent import research

    research(args.question, result_path=args.output)


if __name__ == "__main__":
    main()
