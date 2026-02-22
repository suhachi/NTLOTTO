# NTLOTTO V3 RUNBOOK (운영 매뉴얼 / 고정)

이 문서는 NTLOTTO V3의 “정식 운영 루프”를 고정합니다.
데이터(SSOT) → 리포트(WHY/엔진) → 전략 입력(quota) → 조합 생성(M=50) → 당첨 업로드/채점 → 학습 반영.

---

## 0) 필수 데이터(SSOT 2개)
- data/ssot_sorted.csv  : 정답 판정 유일 기준
- data/ssot_ordered.csv : 분석 피처(추첨 순서) 전용

---

## 1) 리포트 생성(WHY + 엔진별 7종)
### 명령(고정)
```bash
python -m ntlotto.cli.make_reports --round 1213 --long 100 --short 5,10,15,20,25,30
```
### 산출물(고정)
- docs/reports/latest/SSOT_Validation.md
- docs/reports/latest/WHY_Long_R1213.md
- docs/reports/latest/WHY_Short_Trends_R1213.md
- docs/reports/latest/ENG_*_R1213.md (7개)
- docs/reports/latest/ENGINE_SELECTION_TEMPLATE.json

---

## 2) 전략 입력(엔진 ON/OFF + quota) — 텍스트로 입력
### 입력 양식(고정)
아래처럼 한 줄로 입력한다(공백 자유).
예시:
NT4 10 / NT5 10 / NTO 15 / NT-Ω 5 / NT-VPA-1 5 / NT-LL 5 / NT-PAT 0

### 명령(고정)
```bash
python -m ntlotto.cli.set_strategy_cli --round 1213 --M 50 --seed 20260222 --p_max 0.16 --ev_slots_max 5 --fallback_max 5 \
  --text "NT4 10 / NT5 10 / NTO 15 / NT-Ω 5 / NT-VPA-1 5 / NT-LL 5 / NT-PAT 0"
```
### 산출물(고정)
- docs/reports/latest/ENGINE_SELECTION_R1213_M50.json

---

## 3) 예측 조합 생성(M=50) — 전략 파일 기반
### 명령(고정)
```bash
export ALLOW_COMBO_GENERATION=1
python -m ntlotto.cli.generate_combos_cli --round 1213 --selection docs/reports/latest/ENGINE_SELECTION_R1213_M50.json \
  --i_understand_and_allow_generation
```
### 산출물(고정)
- docs/reports/latest/Prediction_Set_R1213_M50.md
- docs/reports/latest/NTUC_1213_M50_combos.csv

---

## 4) 당첨 업로드/채점(추첨순서 입력)
당첨번호는 “추첨순서대로” 입력한다.
예: 8 25 44 31 5 41 bonus 45

### 명령(고정)
```bash
python -m ntlotto.cli.score_round_cli --round 1213 --combos docs/reports/latest/NTUC_1213_M50_combos.csv \
  --ordered "8 25 44 31 5 41" --bonus 45
```
### 산출물(고정)
- docs/reports/latest/Score_R1213.md
- docs/reports/latest/Score_R1213.csv

---

## 5) 학습/반영(엔진 평가/가중치 업데이트)
(선택) 엔진 성과를 번호단위로 평가하고, 다음 회차 전략 참고 자료 생성.
```bash
python -m ntlotto.cli.eval_k_cli --K 20 --N 100
python -m ntlotto.cli.update_weights_cli --eval docs/reports/latest/Engine_Eval_K20_N100.json
```

---

## 운영 원칙(강제)
- WHY→전략→예측 레이어를 섞으면 FAIL
- 전략(quota)은 예측 결과에 100% 반영되어야 한다(Actual==Quota)
- 헌법(중복/쏠림)은 전역 적용, 위반 시 FAIL
