# Contract: NT-Ω (NT-Omega)

## 1. 목적 (Purpose)
NT-Ω 엔진은 개별 엔진들(또는 NTO 메타엔진)로부터 후보 번호(및 패턴)의 스코어 맵을 입력받아, "최종 포트폴리오(예측 조합) 선택을 위한 핵심 점수 엔진" 역할을 합니다. 하지만 계약 우선 원칙에 따라, 별도 지시가 없는 한 **Ω 후보 풀(K_pool=22) 산출까지만** 담당하며 실제 번호 조합 생성은 하지 않습니다.

## 2. 입력 (Input)
- **Data Source**: `ssot_sorted.csv` 및 `NTO` 스코어 맵, 기타 활성 엔진들(NT4, NT5, NT-LL, VPA 등)의 진단 스코어.
- **Target Round ($R$)**: 대상 회차.

## 3. 알고리즘 및 득점 로직 (Algorithm & Scoring)
- **1단계: 점수 산출(Ω Score Map)**
  - NTO 메타 옵티마이저 등지에서 수집한 엔진별 스코어 합산(가중합: $\sum w_E \cdot S_E$).
  - 각 엔진이 보유한 '과거 성과 K_eval=20'표에 기반한 "최근 20회차 기반 Ω 가중치 업데이트" 룰을 실행하여 $w_E$ 확보. (보통은 NTO가 처리하지만, 오메가 고유의 성과 반영 로직을 구현할 수 있음).
- **2단계: 최적화 풀 K_pool 추출**
  - $\Omega(n)$ 점수가 가장 높은 상위 22개 번호를 추출.
- **3단계: 가중치 업데이트(Weight Update)**
  - 최근 평가 회차 $R-1$ 등 K_eval=20 범위에서 엔진별 히트수, 리콜 등을 기준으로 기존 가중치를 "학습률(Learning Rate)" $\eta$와 정규화(Normalization, Clip) 방식을 차용해 스무딩(Exponential Smoothing 등) 업데이트.

## 4. 출력 (Output)
- **Format**: `EngineOutput`
  - `engine`: "NT-OMEGA"
  - `round`: 타겟 라운드 ($R$)
  - `scores`: 1~45의 최종 $\Omega$ 스코어 및 기여 엔진/피처 세부정보 딕셔너리 리스트.
  - `topk`: `scores` 기준 상위 22개 (K_pool=22) 번호 리스트. 
    - (주의: 타 파이프라인 엔진들은 `k_eval=20`을 반환하지만 본 엔진은 고유하게 `22`개를 기본 반환합니다.)
  - `metrics`: 업데이트 된 새로운 오메가 가중치 상태 로그 (`weight_updated`, `engine_hit_kpi`).

## 5. 제약사항 (Constraints)
- 명시적 지시가 없는 한 “6개 최적 조합 추천 포트폴리오”를 절대 생성/출력하지 않습니다.
- 점수 스케일은 반드시 $[0, 1]$ 또는 Z-score. `NaN`, `Inf` 에러에 대한 강건성(Robust) 처리 필수.
