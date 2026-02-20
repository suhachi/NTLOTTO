# Contract: AL1, AL2, ALX (리포트 강화용 엔진)

## 1. 목적 (Purpose)
AL 시리즈(AL1, AL2, ALX)는 주로 "추첨 순서(Draw Order)" 또는 "인접 간격(Gap)/전이(Transition) 확률" 같은 심화 마르코프 특성을 다루는 분석기입니다. 그러나 본 계약에 따라 현재 이들은 기본적으로 **가중치 미반영(No Weight in Meta)** 상태이며, "분석 리포트 품질 강화용 (설명용 진단 패킷 생성)" 스터브 모듈로 취급됩니다.

## 2. 입력 (Input)
- **Data Source**: `ssot_ordered.csv`, `ssot_sorted.csv` (AL 엔진은 `both` 허용)
- **Target Round ($R$)**: 평가 대상 회차.

## 3. 알고리즘 및 득점 로직 (Algorithm & Reporting)
- 실질적 예측 점수(Prediction Score map)는 모두 균등(Equal, 예: 0.5) 리턴. (또는 기본 오프).
- 대신 `diagnostics(context)` 메서드를 통해 다음의 정보를 `evidence pack` 형태로 요약/산출:
  - **AL1**: 끝수 트렌드 및 과열 경고 (최근 10회차 기준 끝수 0~9 분포 편차 요약 등)
  - **AL2**: Pair heatmap 트렌드 요약 (최근 특정 빈도로 같이 출현한 번호 쌍 요약)
  - **ALX**: 밴드 이동 및 변동성, 마르코프 체인 기반 전이 확률 요약 등.
- report.ts 훅에 걸려 엔진 리포트 마크다운에 섹션으로 추가됨.

## 4. 출력 (Output)
- **Format**: `EngineOutput`
  - `engine`: "AL1" | "AL2" | "ALX"
  - `scores`: 모두 균등한 점수(예: 0.5) 맵.
  - `topk`: `None` 또는 빈 리스트 (실제 추천에 개입하지 않음).
  - `diagnostics`: 분석 요약 텍스트 및 마크다운/JSON 파싱용 지표 데이터 (`evidence pack`).
    - 생성된 마크다운 섹션은 오케스트레이터에서 종합 리포트 생성 시 결합됨.

## 5. 제약사항 (Constraints)
- 추첨순서를 참조하더라도 엔진의 추천 기능(TopK)에 절대 가중치를 영향을 주지 않아야 함. (계약상 명시됨).
- 리포트 생성 시 에러가 나거나 런타임에 실패하면 빈 딕셔너리로 조용히 Fallback 할 것 (안정성 최우선).
