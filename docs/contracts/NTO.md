# Contract: NTO (Integrative Meta Optimizer)

## 1. 목적 (Purpose)
NTO 모듈은 여러 기본 개별 엔진(Base Engines)들의 스코어 맵 및 TopK 리스트를 입력받아 조합/보정하고, 새로운 메타 점수(Meta Score)를 산출하는 옵티마이저입니다.

## 2. 입력 (Input)
- **Data**: 여러 독립된 엔진들(NT4, NT5, NT-LL, VPA, NT-VPA-1 등)의 `EngineOutput` (점수 맵 포함).
- **Target Round ($R$)**: 평가 대상 회차.
- **엔진 가중치 (Engine Weights)**: $\Omega$ 가중치 세트 또는 NTO 내부의 Learning weight.

## 3. 알고리즘 및 결합 로직 (Algorithm & Aggregation)
- NTO는 다음 세 가지 결합 로직을 지원/구현합니다 (계약상 필수):
  1. **Rank-based Aggregation (Borda Count)**
     - 각 엔진 $E$에서 번호 $n$의 순위 $r_{E}(n)$에 대해 점수를 $K_{max} - r_{E}(n) + 1$ (범위 외는 0) 부여 후 합산.
  2. **Score-based Weighted Sum**
     - 각 엔진의 산출 점수를 z-score 내지 min-max 정규화 한 후(Calibration Step), 현재 엔진 가중치 벡터 $w$를 곱해 합산.
     - $Score_{NTO}(n) = \sum_{E} w_E \cdot \text{norm}(Score_E(n))$
  3. **Weight Update Rule (메타 가중치 업데이트)** 
     - 단일 엔진이 아닌 "가중치 옵티마이징"의 경우:
       이전 회차(K_eval=20 성과)에 기반하여 각 엔진의 가중치 $w_E$를 업데이트 (기본값 균등 분배 1/N에서 시작, 과적합 방지를 위한 클립(clip) 및 학습률 $\eta$ 적용).

## 4. 출력 (Output)
- **Format**: `EngineOutput` 형태 준수
  - `scores`: 최종 Meta Score 기준 $1 \dots 45$ 번호 목록.
  - `topk`: `Score_{NTO}` 기준 Top 20 번호 리스트.
  - `engine_contributions`: 상위 TopK 도출 시 어떤 엔진이 얼만큼 기여했는지 퍼센티지로 표시된 맵. $E \to \%$ 형태.

## 5. 제약사항 (Constraints)
- NTO 역시 특정 번호 조합을 스스로 만들어내지 않으며, 모든 결과는 후보군 리스트와 점수 맵으로 끝납니다.
- 누락되거나 에러가 난 스터브(Stub) 입력 엔진은 동적으로 가중치 0 처리하여 정상 계산을 진행해야 합니다. 
