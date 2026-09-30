def validate_question(question):
    if not isinstance(question, str):
        raise TypeError("Question type must be string")

    question = question.strip()

    if not question:
        raise ValueError("Question must be non-empty")

    return question


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

    print("self-check passed")
