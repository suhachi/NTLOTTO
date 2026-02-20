# Contract: NT-VPA-1 Engine

## 1. 목적 (Purpose)
NT-VPA-1은 VPA 엔진의 득점 결과에 "국소 편차 교정(Local Deviation Correction, NT-LL 개념)"을 적용하여 안정성 지표를 보완한 하이브리드 엔진입니다. 

## 2. 입력 (Input)
- **Data Source**: `ssot_sorted.csv`
- **Target Round ($R$)**: 평가/예측 대상 회차
- **Base Score**: VPA 엔진의 점수 맵.
- **Correction Window**: NT-LL에서 사용하는 최근 윈도우 (기본 $W=20$).

## 3. 알고리즘 및 득점 로직 (Algorithm & Scoring)
- **1단계: VPA Raw Score 획득**
  - VPA 명세에 따른 번호별 $Score_{vpa}(n)$ 계산.
- **2단계: 최근 극단값/편차 계산**
  - NT-LL의 $dev(n) = norm(f_{recent}) - norm(f_{global})$ 산출.
- **3단계: Shrinkage (감쇠/보정) 적용**
  - 만약 VPA 득점이 매우 높지만, 최근 편차(dev)가 지나치게 양수(과열)라면 점수를 일정 비율 깎습니다 (Regularization).
  - 공식 제안:
    $Score_{final}(n) = Score_{vpa}(n) - \alpha \cdot \max(0, dev(n))$
    초기 $\alpha = 0.5$ 설정.
- **4단계: Stability (안정성) 지표 산출**
  - 편차 절대값 $|dev(n)|$이 작을수록 안정성이 높다고 간주하여 `evidence`에 기록.

## 4. 출력 (Output)
- **Format**: `EngineOutput`
  - `engine`: "NT-VPA-1"
  - `round`: 타겟 라운드 ($R$)
  - `scores`: $\{n, score, evidence, stability\}$ 리스트.
    - `evidence`: VPA 근거와 함께 "Penalty applied due to +dev" 등의 교정 내역 포함.
  - `topk`: `score` 내림차순 -> `n` 오름차순 결과 상위 20개 리스트.

## 5. 제약사항 (Constraints)
- **결정론/계약 우선**: 동일 VPA 점수와 동일 이력에서는 반드시 동일한 보정 점수가 산출되어야 합니다.
- 타 엔진과 동일한 평가 프레임워크와 Output 스키마를 따릅니다.
