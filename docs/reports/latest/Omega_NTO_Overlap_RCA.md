# Omega vs NTO Overlap Root Cause Analysis (RCA)

## 1. 개요
Sprint 4 백테스트 과정에서 NT-Omega 포트폴리오와 NTO 포트폴리오의 일치도(Jaccard@20)가 모든 라운드에서 1.000 (100% 동일)으로 산출되는 증상이 발견되었습니다. 해당 증상의 원인을 파악하고 재현 고정 및 수정 패치를 수행했습니다.

## 2. 원인 판정
**판정 결과: (원인 1) Ω가 NTO의 score_map을 그대로 반환/재정렬만 함**

### 2.1. 증거 (정적 코드 분석)
`nt_lotto/nt_engines/nt_omega.py` 파일의 내부 로직에서 다음과 같은 패스스루(Pass-through) 하드코딩이 발견되었습니다.

```python
    # 2. Omega specific adjustments (e.g., historical hits momentum)
    # Omega can maintain a small internal momentum or just pass through NTO if it's purely a selector
    omega_scores = {}
    for n in range(1, 46):
        # Default pass-through in this implementation
        omega_scores[n] = float(base_scores.get(n, 0.5))
```
NTO의 `base_scores`를 0.0부터 1.0까지 그대로 `omega_scores`에 복사한 뒤 정렬하여 K_pool 개수를 반환하고 있었으므로, Top20 집합이 NTO의 Top20과 필연적으로 100% 동일해졌습니다.

## 3. 적용한 패치 요약 (C-2)
"Ω 독자 조정" 요소를 추가하여 독립성을 부여했습니다.

1. **독립 신호 (Momentum) 부여:** 최근 10회차의 번호별 출현 빈도를 `0.0 ~ 1.0`으로 MinMax 정규화한 "단기 모멘텀(Recent Frequency)" 지표를 생성합니다.
2. **소프트 스케일 조정 (λ 팩터 적용):** 기존 `normalize(NTO Base)` 에 `λ * normalize(Momentum)` 구조를 차용하여, `omega_score_n = base_score_n + 0.15 * momentum_n` 으로 합산했습니다.
3. **타이브레이커 및 재정렬:** 스코어가 합산되면서 랭킹 우선순위에 변동이 발생하며, Jaccard 지수가 1.0 미만으로 떨어져 독자적인 필터링 역할을 정상적으로 수행하게 됩니다. (`tests/test_omega_nto_independence.py` 로 회귀 테스트 고정 완료)
