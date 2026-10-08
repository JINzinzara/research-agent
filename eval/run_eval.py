import json
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

from research_agent import agent

CASES_PATH = Path(__file__).with_name("cases.jsonl")


def load_cases(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run_case(case):
    if case["price"] is None:
        price_patch = patch.object(
            agent,
            "get_price",
            side_effect=RuntimeError("price unavailable"),
        )
    else:
        price_patch = patch.object(
            agent,
            "get_price",
            return_value=case["price"],
        )

    if case["news"] is None:
        news_patch = patch.object(
            agent,
            "get_news",
            side_effect=RuntimeError("news unavailable"),
        )
    else:
        news_patch = patch.object(
            agent,
            "get_news",
            return_value=case["news"],
        )

    with (
        patch.object(
            agent,
            "extract_request",
            return_value=case["request"],
        ),
        price_patch,
        news_patch,
        patch.object(
            agent,
            "synthesize",
            return_value="테스트 답변",
        ) as mock_synthesize,
        patch("builtins.print"),
    ):
        result = agent.research(case["question"])

    assert result["request"] == case["request"], case["id"]
    assert result["status"] == case["expected_status"], case["id"]

    expected_warnings = case["expected_warning_prefixes"]
    assert len(result["warnings"]) == len(expected_warnings), case["id"]

    for prefix in expected_warnings:
        assert any(
            warning.startswith(prefix) for warning in result["warnings"]
        ), f"{case['id']}: missing warning {prefix}"

    assert mock_synthesize.call_count == int(case["expect_synthesis"]), case["id"]

    assert datetime.fromisoformat(result["collected_at"]).tzinfo is not None

    if case["price"] is None:
        assert "CoinGecko price" not in result["sources"]
    else:
        assert "CoinGecko price" in result["sources"]

    if case["news"]:
        assert "CoinDesk news 1" in result["sources"]

    if case["price"] is None and not case["news"]:
        assert result["sources"] == ("Sources:\n- No sources collected")

    return result


def main():
    cases = load_cases(CASES_PATH)

    for case in cases:
        run_case(case)
        print(f"PASS: {case['id']}")

    print(f"{len(cases)} evaluation cases passed")


if __name__ == "__main__":
    main()
