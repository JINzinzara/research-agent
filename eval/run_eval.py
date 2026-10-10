"""Run deterministic pipeline evaluations with mocked collectors and synthesis"""

import json
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from research_agent import agent

CASES_PATH = Path(__file__).with_name("cases.jsonl")


def load_cases(path):
    """Load non-empty JSONL evaluation records from a UTF-8 file"""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run_case(case):
    """Check one pipeline fixture using fixed clocks and mocked external calls"""
    case_id = case["id"]

    # Preserve expected values if a function mutates its inputs.
    test_data = deepcopy(case)
    expected_news = case["news"] or []

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
            return_value=test_data["price"],
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
            return_value=test_data["news"],
        )

    # Fix the request just before KST midnight and finish just after it.
    fixed_reference = datetime(2026, 10, 8, 14, 59, 59, tzinfo=timezone.utc)
    fixed_completed = fixed_reference + timedelta(seconds=2)

    with (
        patch.object(agent, "datetime", wraps=datetime) as mock_clock,
        patch.object(
            agent,
            "extract_request",
            return_value=test_data["request"],
        ) as mock_extract,
        price_patch as mock_price,
        news_patch as mock_news,
        patch.object(
            agent,
            "synthesize",
            return_value="테스트 답변",
        ) as mock_synthesize,
    ):
        mock_clock.now.side_effect = [fixed_reference, fixed_completed]
        result = agent.research(case["question"])

    # Check request and collection arguments.
    mock_extract.assert_called_once_with(case["question"])
    mock_price.assert_called_once_with(
        case["request"]["coin_id"],
        case["request"]["currency"],
    )
    mock_news.assert_called_once_with(
        case["request"]["news_query"],
        datetime.fromisoformat(result["news_window"]["start"]),
        fixed_reference,
    )

    # Check returned evidence and status.
    assert result["request"] == case["request"], case_id
    assert result["price"] == case["price"], case_id
    assert result["news"] == expected_news, case_id
    assert result["status"] == case["expected_status"], case_id

    # Check missing-data and collection warnings.
    expected_warnings = case["expected_warning_prefixes"]
    assert isinstance(result["warnings"], list), case_id
    assert len(result["warnings"]) == len(expected_warnings), case_id

    for prefix in expected_warnings:
        assert any(
            warning.startswith(prefix) for warning in result["warnings"]
        ), f"{case_id}: missing warning {prefix}"

    # Check synthesis gating and evidence forwarding.
    assert isinstance(result["answer"], str), case_id

    if case["expect_synthesis"]:
        mock_synthesize.assert_called_once_with(
            case["question"],
            case["request"],
            case["price"],
            result["news_window"],
            result["news_groups"],
        )
        assert result["answer"] == "테스트 답변", case_id
    else:
        mock_synthesize.assert_not_called()
        assert result["answer"].startswith("수집된 근거가 없어"), case_id

    # Keep generation time separate from the fixed request cutoff.
    collected_at = datetime.fromisoformat(result["collected_at"])

    assert collected_at.utcoffset() == timedelta(
        0
    ), f"{case_id}: collected_at must be UTC"
    assert (
        collected_at == fixed_completed
    ), f"{case_id}: collected_at must match the completion time"
    assert result["news_window"] == {
        "start": "2026-10-06T15:00:00+00:00",
        "end": fixed_reference.isoformat(),
    }, f"{case_id}: news window must use the reference time"
    # Check source links and publication timestamps.
    expected_source_lines = []

    if case["price"] is not None:
        expected_source_lines.append(
            f"- [CoinGecko price]({case['price']['source_url']})"
        )

    for idx, article in enumerate(case["news"] or [], start=1):
        published_at = article.get("published_at") or "Unknown"
        expected_source_lines.append(
            f"- [CoinDesk news {idx}]({article['source_url']})"
            f" - Published: {published_at}"
        )

    if expected_source_lines:
        expected_sources = "Sources:\n" + "\n".join(expected_source_lines)
    else:
        expected_sources = "Sources:\n- No sources collected"

    assert result["sources"] == expected_sources, case_id

    return result


def main():
    cases = load_cases(CASES_PATH)

    for case in cases:
        run_case(case)
        print(f"PASS: {case['id']}")

    print(f"{len(cases)} evaluation cases passed")


if __name__ == "__main__":
    main()
