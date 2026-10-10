# research-agent

## Purpose

크립토 시장을 빠르게 파악하려는 개인 투자자를 위한 가격 데이터와 최신 뉴스를 근거로 답변하는 리서치 에이전트이다. 해당 에이전트는 정보 탐색 및 비교 시간을 줄이고, 답변에 대한 출처를 명확히 한다. 다만 자동 거래와 종목 추천을 제공하지 않는다.

## Workflow

```
question -> get asset·currency -> fetch market data·news -> organize evidence -> answer + sources
```

## Result

1. 요약 및 신호 (Summary & Signal)
    - 질문에 대한 요약 답변: 사용자의 질문 의도를 파악하여 1~2줄로 핵심만 요약한 답변

2. 정량적 시장 데이터 (Quantitative Data)
    - 현재 가격 (Current Price): 조회 시점의 자산 가격과 통화
    - 24시간 변동률 (24h Change %): 24시간 전 대비 등락률

3. 정성적 뉴스 및 정보 (Qualitative News)
    - 자산명이 포함된 RSS 기사 최대 5개의 헤드라인 및 요약. 지정 기간 안 기사를 우선하고, 남는 자리는 기간 밖·발행 시각 미상 참고 자료로 채운다.

4. 신뢰성 및 메타데이터 (Provenance & Metadata)
    - 출처 URL (Source URLs): 수집된 뉴스 및 가격 데이터의 원본 링크 (답변 근거 확인용)
    - 가격 갱신 시각, 기사 발행 시각, 결과 생성 시각을 구분해 표시한다. `collected_at`은 결과 생성 시각이며 개별 자료의 수집 시각이 아니다.
    - 수집 데이터 제공자(Provider) 명시: 데이터 신뢰도 검증용 출처 표기

5. 예외 처리 및 경고 (Error Handling & Warnings)
    - 데이터가 없을 때 (Fallback Warning): 특정 API 점검이나 거래 중지 등으로 데이터를 가져오지 못할 때 오류 메시지
    - 누락 항목을 명시하고 추정값은 생성하지 않음

## News window

- 수동 리서치의 뉴스 범위: 전날 KST 00:00 이상부터 실행 시작 시각 `reference_at` 미만까지.
- `end`는 모델 답변 생성이 끝나는 `collected_at`과 별개이며 실행 시작에 고정한다.
- 기간 길이는 조회 시각에 따라 달라진다. 전일 하루나 최근 24시간 뉴스라고 부르지 않는다.
- 가격의 rolling 24시간 변동률은 이 뉴스 기간의 수익률이 아니다.
- 현재 RSS 피드에서 확보한 기사만 대상으로 하며 기간 전체의 뉴스를 보장하지 않는다.
- 아침 정기 브리핑·스케줄·알림은 아직 구현하지 않았다.

## Offline demo

API 키와 외부 API 호출 없이 저장소 루트에서 실행하는 방법

```bash
PYTHONPATH=src python3 -m research_agent.briefing eval/briefing_result.json
```

- 출력: 상태, KST 뉴스 기간, 생성 시각, 경고, 답변, 출처
- 저장된 예제 데이터를 재생
- 최신 시장 데이터 조회나 실제 모델 품질을 검증하는 기능 아님
