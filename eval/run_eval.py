import json
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch


from research_agent import agent

CASES_PATH = Path(__file__).with_name("cases.jsonl")


def load_cases(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def run_case(case):
    case_id = case["id"]

    # 함수 내부에서 입력을 변경하여도 원본 기대값 유지
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

    started_at = datetime.now(timezone.utc)

    with (
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
        patch("builtins.print"),
    ):
        result = agent.research(case["question"])

    finished_at = datetime.now(timezone.utc)

    # 요청 및 수집 조건
    mock_extract.assert_called_once_with(case["question"])
    mock_price.assert_called_once_with(
        case["request"]["coin_id"],
        case["request"]["currency"],
    )
    mock_news.assert_called_once_with(case["request"]["news_query"])

    # 반환 근거 및 상태
    assert result["request"] == case["request"], case_id
    assert result["price"] == case["price"], case_id
    assert result["news"] == expected_news, case_id
    assert result["status"] == case["expected_status"], case_id

    # 누락·실패 경고
    expected_warnings = case["expected_warning_prefixes"]
    assert isinstance(result["warnings"], list), case_id
    assert len(result["warnings"]) == len(expected_warnings), case_id

    for prefix in expected_warnings:
        assert any(
            warning.startswith(prefix) for warning in result["warnings"]
        ), f"{case_id}: missing warning {prefix}"

    # 답변 합성 여부 및 전달 근거
    assert isinstance(result["answer"], str), case_id

    if case["expect_synthesis"]:
        mock_synthesize.assert_called_once_with(
            case["question"],
            case["request"],
            case["price"],
            expected_news,
        )
        assert result["answer"] == "테스트 답변", case_id
    else:
        mock_synthesize.assert_not_called()
        assert result["answer"].startswith("수집된 근거가 없어"), case_id

    # 결과 생성 시각: UTC 기준, 이번 실행 범위 안에 있는가
    collected_at = datetime.fromisoformat(result["collected_at"])

    assert collected_at.utcoffset() == timedelta(
        0
    ), f"{case_id}: collected_at must be UTC"
    assert (
        started_at <= collected_at <= finished_at
    ), f"{case_id}: collected_at is outside this run"

    # 전체 출처 목록 및 기사 발행 시각
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
