# SSOT 안내 (00_데이터베이스/SSOT)

## 목적
- 추첨순서(n1~n6)와 보너스를 **단일 진실원천(SSOT)** 으로 관리
- 기존 추첨순서 파서 및 향후 NT-2/NT-BONUS 엔진이 그대로 사용 가능하도록 표준 스키마 제공

## 산출물
- `SSOT/draw_order.csv`: round,n1..n6,bonus,(draw_date,year,source)
- `SSOT/winning_sorted.csv`: round,s1..s6,bonus ← draw_order.csv에서만 파생
- `SSOT/draw_order.md`: 가독용 테이블 (회차 | 1~6 | 보너스)
- `SSOT/_meta.json`: 생성 시각, 입력 소스, row_count, draw_order.csv sha256
- `result/SSOT_VALIDATION_REPORT.md`: 검증 결과 요약

### 예측 모델/엔진 SSOT
- `nt_vnext/NT_vNext_PREDICTION_SSOT_v1.0.md`: 엔진별 정의 및 공식 표준
- `nt_vnext/methods/`: 개별 엔진별 상세 기술서 (definition, formula, README)

## 레거시 소스 (삭제 금지)
- `00_데이터베이스/로또-추첨순서-데이터.md`
- `00_데이터베이스/로또-회차별-당첨번호.md`
- `00_데이터베이스/당첨번호.csv`
- `00_데이터베이스/회차별_당첨번호_합계표.md`

SSOT는 위 레거시 자료를 읽어 교차검증 후 생성되며, 레거시 파일은 참조용으로만 유지합니다.

## 마이그레이션 가이드 (요약)
- 신규 코드: `SSOT/draw_order.csv`를 기본 입력으로 사용
- 정렬된 당첨번호가 필요하면 `SSOT/winning_sorted.csv` 사용 (직접 정렬 금지)
- 데이터 검증 시 `result/SSOT_VALIDATION_REPORT.md`를 확인

## 생성/검증 명령
```
python scripts/build_ssot_draw_order.py
python scripts/validate_ssot_draw_order.py
```
