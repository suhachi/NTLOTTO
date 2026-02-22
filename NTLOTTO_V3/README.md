# NTLOTTO v3 (Code Name: Nano)

NTLOTTO v3 프로젝트는 철저히 검증된 SSOT(Single Source of Truth) 기반의 파이프라인으로 구성되어 있습니다.

## 운영 철학 및 주요 원칙
1. **SSOT 2파일 원칙**: 모든 분석 및 판정은 외부 데이터 연동 없이 `/mnt/data/`에서 복사된 `ssot_sorted.csv`와 `ssot_ordered.csv` 2개의 파일에만 의존합니다. 정답 판정은 오직 `ssot_sorted.csv`만을 기준으로 합니다.
2. **WHY → 전략 → 예측 분리**: 데이터 분석(WHY)과 엔진 모델을 활용한 후보 도출(전략), 그리고 실제 출력 조합을 생성하는 모듈(예측) 레이어를 엄격히 분리하여, 서로 의존하지 않도록 격리했습니다.
3. **각 엔진의 독립적 후보풀 유지**: 한 방향으로 수렴하는 것을 막기 위해, 각 엔진은 평가 가중치에 따라 조합할 후보풀을 공유하지 않고 개별적으로 반환합니다.

## 디렉토리 및 리포트 산출물 경로
- `data/`: SSOT 데이터 원본(`ssot_sorted.csv`, `ssot_ordered.csv`)
- `src/`: 핵심 모듈(`core`, `reports`, `engines`, `predict`, `score`, `cli`)
- `docs/reports/latest/`: 가장 최근 실행된 각종 통계 리포트, 예측 조합 결과, 엔진 평가 및 가중치 업데이트 파일 저장소
- `docs/reports/history/`: 과거 버전 문서 백업소
- `docs/reports/dev_test/`: 테스트 전용 산출물 보관소 (운영 혼입 금지)

## 조합 생성 안내 (기본 OFF)
NTLOTTO v3에 포함된 조합 생성 기능(`generate_combos_cli.py`)은 **기본적으로 무조건 OFF 상태**이며, 무분별한 사용을 막기 위해 **2중 잠금**이 걸려있습니다. 
조합을 생성하려면 다음 두 조건을 충족하여 실행해야 합니다:
1. 환경변수 `ALLOW_COMBO_GENERATION=1` 설정
2. 실행 시 `--i_understand_and_allow_generation` CLI 플래그 명시

(실행 예시: `bash scripts/run_sprint_c_generate.sh` 참조)

## 추첨 후 채점 및 학습 실행 방법 (Sprint D/E)
새로운 회차의 당첨 번호가 SSOT 데이터에 업데이트된 이후, 아래의 실행 단계를 거쳐 채점과 엔진 학습(가중치 업데이트)을 수행할 수 있습니다.

### 1) 채점 실행 (Sprint D)
생성했던 예측 조합 CSV 파일과 실제 결과(SSOT)를 비교하여 등수를 매깁니다.
```bash
bash scripts/run_sprint_d_score.sh
# 내부적으로 아래 커맨드를 포함합니다:
# python -m ntlotto.cli.score_round_cli --round 1212 --combos docs/reports/latest/NTUC_1212_combos.csv
```
-> 출력: `Score_R{R}.md` 및 `Score_R{R}.csv`

### 2) 엔진 성과 평가 & 가중치 업데이트 (Sprint E)
과거 추천 내역을 추적하여 엔진별 K_eval(예: 20개 추출) 성과(Recall 등)를 평가하고 지표를 통해 향후 가중치를 업데이트합니다.
```bash
bash scripts/run_sprint_e_eval_update.sh
# 내부 평가 측정: python -m ntlotto.cli.eval_k_cli --k 20 --n 100
# 내부 가중치 갱신: python -m ntlotto.cli.update_weights_cli --eval_json docs/reports/latest/Engine_Eval_K20_N100.json
```
-> 출력: `Engine_Eval_K20_N100.md / .json` 및 `Weights_Rationale.md`, `Weights_Updated.json`
