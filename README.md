# research-agent

가격과 RSS 기사에 근거해 한국어·영어 브리핑을 생성하는 크립토 리서치 도구.
지원 자산은 Bitcoin·Ethereum·Solana, 통화는 USD·KRW다.
매매 추천·자동 거래·개인 계정 연동은 제공하지 않는다.

## Current contract

- 뉴스 기간: 전날 KST 00:00 이상부터 리서치 시작 시각 `reference_at` 미만까지.
- 기사: 피드 전체의 자산명 매칭 결과에서 기간 안 기사를 우선해 최대 5개 선택.
  남는 자리는 기간 밖·발행 시각 미상 참고 자료로 채운다. 각 그룹 안에서는 피드 순서를 유지한다.
- 가격의 rolling 24시간 변동률과 뉴스 기간의 수익률은 다르다.
- 가격 갱신 시각·기사 발행 시각·결과 생성 시각을 구분한다.
  `collected_at`은 결과 생성 시각이며 개별 자료 수집 시각이 아니다.
- 반환 필드: `request`, `price`, `news`, `answer`, `sources`, `status`,
  `warnings`, `collected_at`, `news_window`, `news_groups`.
- 상태: `ok` / 누락·수집 한계가 있는 `partial` / 가격과 뉴스 근거가 모두 없는 `failed`.
- 수집 근거가 모두 없으면 답변 합성을 생략한다. 누락 수치·시각을 추정하지 않는다.
- JSON은 기존 파일을 덮어쓰지 않는다. `research()`는 결과를 반환·선택적으로 저장하고,
  터미널 출력은 CLI가 담당한다.

## Structure

- `src/research_agent/agent.py`: 수집·합성·경고·결과 반환의 전체 흐름.
- `src/research_agent/collectors.py`: CoinGecko Demo 가격과 CoinDesk RSS 수집.
- `src/research_agent/generation.py`: 질문·계획 검증, 요청 해석, 근거 기반 답변 생성.
- `src/research_agent/periods.py`: UTC 정규화, KST 기간 계산, 기사 기간 분류.
- `src/research_agent/briefing.py`: 출처·브리핑 표시, JSON 저장, 저장본 재생.
- `src/research_agent/cli.py`: 실제 실행 인자 처리와 터미널 출력.
- `tests/`: 외부 호출 없는 단위·통합 검사.
- `eval/`: 평가 입력, 평가 runner, 보존한 실제 모델 답변·실행 결과.

## Live research

저장소 루트에서 실행한다. 기존 Python 환경에 `openai`, `coingecko-sdk`,
`pydantic`이 필요하고, `OPENAI_API_KEY`와 Demo 키인 `COINGECKO_API_KEY`가 설정돼 있어야 한다.
모델은 `gpt-6-astra`다. 키는 코드·JSON·Git에 저장하지 않는다.

```bash
mkdir -p outputs
PYTHONPATH=src python3 -m research_agent.cli "비트코인의 USD 가격과 전날 00시부터 조회 시각까지의 뉴스를 요약해줘." --output outputs/briefing.json
```

실제 조회와 유료 모델 요청이 발생한다. 기존 저장본은 아래 재생 명령으로 확인한다.
동일 출력 경로로 실제 리서치를 재실행하면 저장 단계에서 거절되지만,
그 전에 API 요청은 발생할 수 있으므로 성공한 실행을 반복하지 않는다.

## Offline demo

API 키와 외부 호출 없이 저장소 루트에서 실행한다.

```bash
PYTHONPATH=src python3 -m research_agent.briefing eval/briefing_result.json
```

상태·KST 뉴스 기간·생성 시각·경고·답변·출처를 표시한다.
저장된 예제 데이터의 재생이며 최신 조회나 모델 품질 검증이 아니다.
`eval/outputs/`의 보존 결과도 같은 명령의 파일 인자로 재생할 수 있다.
이전 계약으로 생성된 결과는 당시의 기간과 답변을 그대로 보존한다.

## Offline checks

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

API 키 없이 실행한다. 수집·모델 호출을 mock으로 대체하며,
기존 JSONL 평가 8개도 같은 명령에 포함한다.
실제 모델의 답변 품질·최신 RSS 제공 범위를 이 검사만으로 보장하지 않는다.

## Limits

- RSS는 과거 전체 기사 검색이 아니다. 최대 5개 선택도 기간 전체의 뉴스 확보를 보장하지 않는다.
- 자산명 문자열 매칭이며 거시 사건·의미적 관련성·기사 본문 검증은 구현하지 않았다.
- 가격 최신성의 허용 기준은 아직 확정하지 않았다.
- 개인화 프로필·사용자 조건 알림·아침 스케줄·Telegram 전달은 미구현이다.
