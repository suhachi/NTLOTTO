# [작업 보고서] NT 프로젝트 아키텍처 v2.0 스캐폴딩 Baseline 확립 및 SSOT 반영

**문서 번호**: NT-WCR-20260216-FINAL  
**작성 일자**: 2026-02-16  
**작성자**: NT System Architect (Copilot)  
**상태**: **Scaffolding/Baseline 구축 완료 + 엔진 로직 이식 대기**  
*(유닛 테스트 통과는 스캐폴딩 레벨에 한함, 전체 로직 검증은 추후 구현 필요)*

---

## 1. 개요 (Overview)

본 작업은 NT 프로젝트의 운영 안정성을 위해 무질서하게 확장된 아키텍처를 SSOT(Single Source of Truth) 기반으로 재정립하고, 운영 자동화 파이프라인의 **뼈대(Skeleton/Scaffolding)** 를 구축하는 것을 목표로 했습니다.

현재 상태는 "완전한 운영 준비(Operational)"가 아니며, **데이터 계약이 확립되고 파이프라인의 골격이 완성된 단계**입니다. 
지금 즉시 운영 런(Run)은 가능하지만, 내부 분석 엔진(`nt_engines`)은 14개가 고정되어 있으나 실제 알고리즘이 비어있는 상태(Stubs)입니다.

---

## 2. 수행 내역 및 정합성 (What Changed)

### 2.1 아키텍처 상태 정의 (Correction)
- 기존 보고서의 **"Operational", "모든 모듈 구현 완료"** 표현을 **"Scaffolding/Baseline 구축 완료"** 로 하향 조정하고 정정합니다.
- 패키지 구조, 데이터 로더, 오케스트레이션 로직은 구현되었으나, 핵심 예측 로직은 스켈레톤 상태입니다.

### 2.2 운영 엔트리포인트 단일화
- 기존에 혼재되어 있던 `run_engines.py`, `run_operational_round.py` 등의 진입점은 폐기되었습니다.
- 모든 운영 작업은 **유일한 엔트리포인트**인 `run_round_pipeline.py`를 통해 수행됩니다.
- 엔진 실행은 이 오케스트레이터 내부의 세부 구현 사항(Internal Implementation Detail)으로 격리되었습니다.

### 2.3 SSOT 데이터 계약 (Data Contract)
- `data/ssot_sorted.csv`: 라벨/적중판정 전용
- `data/ssot_ordered.csv`: AL 엔진 피처 전용 (순서유지)
- `data/ssot_conflicts.csv`: 데이터 불일치 격리 로그
- `data/exclude_rounds.csv`: 분석 제외 회차 관리

### 2.4 엔진 14개 고정 (Engine Contract)
14개 엔진 목록을 확정하고 파일 스캐폴딩을 완료했습니다.
(NT4, NT-Ω, NT5, NTO, NT-LL, VPA, NT-VPA-1, AL1, AL2, ALX, NT-EXP, NT-DPP, NT-HCE, NT-PAT)
현재 이 엔진들은 스켈레톤 함수(`analyze`)만 보유하고 있습니다.

### 2.5 Core 모듈 범위 정의 (Scope)
"구현 완료"라고 확정할 수 있는 코어 모듈은 아래와 같습니다.
- `constants.py`: 전역 상수 및 경로
- `ssot_loader.py`: SSOT 로드 및 제외처리
- `features_sorted.py` / `features_ordered.py` : 기초 피처 추출기 (초안)
- `backtest.py` : 평가 로직 (초안)

(`scoring.py`, `kpi.py`, `omega.py`는 기능 구현은 되어 있으나, 실제 데이터 기반 검증 전이므로 '구축 완료'보다 '기능 구현' 단계로 분류합니다.)

---

## 3. 시스템 구조 및 실행

### 3.1 표준 디렉토리 구조
```text
<repo_root>/
├── nt_lotto/
│   ├── scripts/
│   │   └── run_round_pipeline.py  (★ 유일 엔트리포인트)
│   ├── nt_core/
│   │   ├── constants.py
│   │   ├── ssot_loader.py
│   │   └── ...
│   └── nt_engines/
│       ├── nt4.py (Stub)
│       └── ...
```

### 3.2 운영 파이프라인 검증 (Smoke Test)
본 파이프라인은 다음 4단계를 순차적으로 수행하며, 실제로 동작함(Dry-run)을 확인했습니다.
1. **SSOT Load**: 제외 회차를 반영하여 데이터를 메모리에 로드
2. **Backfill**: R회차에 대해 엔진을 구동하고 Recall@20을 산출
3. **Integration**: 성과 기반 Ω 가중치 업데이트 (Softmax)
4. **Predict**: R+1회차 후보풀(Candidate Pool) 생성

**실행 커맨드 (Standard Command / Contract)**
```bash
python -m nt_lotto.scripts.run_round_pipeline --round <RoundNumber> --mode {backfill|next}
```
*   `--round`: 분석 기준 회차 (R)
*   `--mode backfill`: R회차까지만 분석 및 성능 측정 (Prediction 생략)
*   `--mode next`: R회차 분석 후, R+1회차 예측 후보풀 생성 (Operational Default)

**Golden Test (필수 검증 항목)**
1.  **결정론적 재현성 (Determinism)**: 동일 입력(Round/Mode)에 대해 2회 실행 시, 산출된 `omega_pool_K22.csv`의 SHA256 해시가 100% 일치해야 함.
2.  **제외 회차 준수 (Exclusion)**: `data/exclude_rounds.csv`에 명시된 회차는 학습, KPI 산출, 통계 집계에서 완벽히 배제되어야 함.

### 3.3 산출물 아카이빙 확인
파이프라인 실행 시 `03_Global_Analysis_Archive/` 하위에 다음 파일들이 자동 생성됩니다.
- `Rounds/<R>/scoring_<R>.csv` (포트폴리오 채점 결과)
- `KPI/engine_kpi.csv` (엔진별 성과 지표)
- `Omega_Pools/<R>/engine_topk_K20.csv` (엔진 예측값)
- `Omega_Pools/<R+1>/omega_pool_K22.csv` (차기 회차 후보풀)

---

## 4. 결론

NT Project v2.0은 이제 **"무한 확장"의 혼란을 끝내고 "정해진 규칙(Contract)" 위에서 운영될 준비**를 마쳤습니다.
불필요한 스크립트는 삭제되었고, 엔트리포인트는 단일화되었으며, 데이터 흐름은 SSOT를 따릅니다.

남은 과제는 단 하나, 비어있는 `nt_engines/*.py` 파일 내부에 **실제 예측 로직을 이식(Implementation Sprint)** 하는 것입니다.

**상태 확정**: **Scaffolding Ready / Logic Implementation Pending**
