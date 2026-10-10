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
    - 관련 최신 뉴스 리스트: 해당 코인과 직접적인 연관성이 높은 핵심 뉴스 3~5개 헤드라인 및 요약

4. 신뢰성 및 메타데이터 (Provenance & Metadata)
    - 출처 URL (Source URLs): 수집된 뉴스 및 가격 데이터의 원본 링크 (답변 근거 확인용)
    - 데이터 기준 시각 (Timestamp): 데이터가 API나 RSS를 통해 수집된 정확한 UTC/KST 시각
    - 수집 데이터 제공자(Provider) 명시: 데이터 신뢰도 검증용 출처 표기

5. 예외 처리 및 경고 (Error Handling & Warnings)
    - 데이터가 없을 때 (Fallback Warning): 특정 API 점검이나 거래 중지 등으로 데이터를 가져오지 못할 때 오류 메시지
    - 누락 항목을 명시하고 추정값은 생성하지 않음

## Offline demo

API 키와 외부 API 호출 없이 저장소 루트에서 실행하는 방법

```bash
PYTHONPATH=src python3 -m research_agent.briefing eval/briefing_result.json
```

- 출력: 상태, KST 뉴스 기간, 생성 시각, 경고, 답변, 출처
- 저장된 예제 데이터를 재생
- 최신 시장 데이터 조회나 실제 모델 품질을 검증하는 기능 아님