# Contract: VPA (Value-Pattern Aggregation) Engine

## 1. 목적 (Purpose)
VPA 엔진은 "Value-Pattern Aggregation" 로직을 수행합니다. 최근 윈도우(3/5/10/20회차)에서 관측되는 패턴(밴드 편차, 끝수 편차, 홀짝 편차, 번호 쌍(pair) 동반 출현 등)을 집계하여 번호(1~45)별 점수로 환산하는 것이 주 목적입니다.

## 2. 입력 (Input)
- **Data Source**: `ssot_sorted.csv` (반드시 정렬된 당첨 번호 데이터 1~6, 보너스 볼 사용 가능. 추첨순서 데이터는 전이/간격용 참조만 가능, 기본 오프)
- **Target Round ($R$)**: 평가/예측 대상 회차
- **Feature Params**:
  - `window_set`: 기본 [3, 5, 10, 20]
  - `weight_scheme`: 'exp' (최근성 감쇠) 또는 'linear'
  - `feature_weights`: 
    - `band_dev`: 0.3
    - `ending_dev`: 0.3
    - `even_odd_dev`: 0.1
    - `pair_co_occurrence`: 0.3

## 3. 알고리즘 및 득점 로직 (Algorithm & Scoring)
- **패턴 추출**:
  1. 각 윈도우 $W \in \{3, 5, 10, 20\}$에 대해,
  2. **Band (밴드)**: 1~9, 10~19, 20~29, 30~39, 40~45 구간의 출현 빈도를 구하고, 장기 출현 기대값 대비 편차 산출. (해당 밴드에 속한 번호들에 밴드 편차점수 부여)
  3. **Ending (끝수)**: 0~9 끝수별 출현 빈도를 구하고 장기 기대값 대비 편차 산출. (해당 끝수를 가진 번호들에 편차점수 부여)
  4. **Pair (쌍)**: 해당 번호가 최근 윈도우에서 함께 자주 나온 파트너 번호들의 누적 점수를 기반으로 가점 부여.
- **결합 로직 (Aggregation)**:
  $Score_W(n) = W_{band} \cdot P_{band}(n) + W_{ending} \cdot P_{ending}(n) + W_{pair} \cdot P_{pair}(n)$
  $FinalScore(n) = \sum_{W} decay(W) \cdot Score_W(n)$ (여기서 $decay(W)$는 윈도우 크기에 반비례하는 가중치)
  최종 점수는 0~1 사이로 MinMax 정규화되거나 Z-score 기반 확률로 매핑.

## 4. 출력 (Output)
- **Format**: `EngineOutput` (혹은 상술된 `dict` 스키마)
  - `engine`: "VPA"
  - `round`: 타겟 라운드 ($R$)
  - `k_eval`: 20
  - `params`: 사용된 가중치 및 윈도우셋 정보
  - `scores`: 1~45 각 번호의 $\{n, score, evidence\}$ 리스트.
    - `evidence`: ["Band deviation +0.2 in W=5", "Ending freq high in W=10"] 등 문자열 정보
  - `topk`: `scores` 내림차순 정렬 후 추출된 20개 고유 번호 리스트. 
    - 동점 처리: `score` 내림차순 -> `n` 오름차순.

## 5. 제약사항 (Constraints)
- **Look-ahead 방지**: 계산 시 타겟 회차 $R$ 이후의 데이터 참조 절대 불가.
- **결정론 보장**: 난수 생성 및 무작위 정렬 전면 금지.
- 조합 생성 없음. 숫자의 단순 추천 풀 산출까지만 담당.
