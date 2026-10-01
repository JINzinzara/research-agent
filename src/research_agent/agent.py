def validate_question(question):
    if not isinstance(question, str):
        raise TypeError("Question type must be string")

    question = question.strip()

    if not question:
        raise ValueError("Question must be non-empty")

    return question


ASSETS = {
    "bitcoin": "Bitcoin",
    "ethereum": "Ethereum",
    "solana": "Solana",
}

CURRENCY = {"usd", "krw"}


def validate_plan(planned):
    if not isinstance(planned, dict):
        raise TypeError("planned type must be dict")

    coin_id = planned.get("coin_id")
    currency = planned.get("currency")
    news_query = planned.get("news_query")

    if coin_id not in ASSETS:
        raise ValueError("coin_id must be bitcoin, ethereum or solana")
    if currency not in CURRENCY:
        raise ValueError("currency must be usd or krw")
    if news_query != ASSETS[coin_id]:
        raise ValueError("news_query must be Bitcoin, Ethereum or Solana")

    return planned


if __name__ == "__main__":
    assert validate_question(" BTC in USD ") == "BTC in USD"
    try:
        validate_question("    ")
    except ValueError:
        pass
    else:
        raise AssertionError("공백 질문이 ValueError를 발생시키지 않음")

    try:
        validate_question(None)
    except TypeError:
        pass
    else:
        raise AssertionError("None이 TypeError를 발생시키지 않음")

    valid_plan = {
        "coin_id": "ethereum",
        "currency": "usd",
        "news_query": "Ethereum",
    }

    assert validate_plan(valid_plan) == valid_plan
    try:
        validate_plan({"coin_id": "soon", "currency": "usd", "news_query": "Soon"})
    except ValueError:
        pass
    else:
        raise AssertionError("잘못된 입력이 ValueError를 발생시키지 않음")

    try:
        validate_plan(
            {"coin_id": "ethereum", "currency": "usdt", "news_query": "Ethereum"}
        )
    except ValueError:
        pass
    else:
        raise AssertionError("잘못된 입력이 ValueError를 발생시키지 않음")

    try:
        validate_plan(
            {"coin_id": "ethereum", "currency": "usd", "news_query": "Bitcoin"}
        )
    except ValueError:
        pass
    else:
        raise AssertionError("잘못된 입력이 ValueError를 발생시키지 않음")

    try:
        valid_plan(None)
    except TypeError:
        pass
    else:
        raise AssertionError("dict가 아닌 입력이 TypeError를 발생시키지 않음")

    print("self-check passed")
