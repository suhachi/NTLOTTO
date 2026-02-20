# NT Project v2.0 작업 완료 보고서 (Baseline / Scaffolding)

**작성일**: 2026년 2월 15일  
**작성자**: GitHub Copilot (System Architect Agent)  
**상태**: 완료 (Scaffolding / Baseline Established)

---

## 1. 개요 및 목표 달성

본 작업의 목표는 **'NT Project v2.0 아키텍처 개편'을 위한 베이스라인(SSOT/패키지 구조/파이프라인 스캐폴딩) 확립**입니다.  
즉, 본 단계는 “완전 구현(Operational)”이 아니라, **운영 전제조건(Contract/폴더구조/코어 초안/엔진 모듈 뼈대/파이프라인 골격)** 을 마련한 상태입니다.

⚠️ **중요**: 현재 `nt_engines/*.py`는 **뼈대(skeleton)** 단계이며, 실제 분석 알고리즘은 다음 단계에서 **레거시 이식 또는 rules.md 기반 구현**이 필요합니다.

---

## 2. 주요 구현 내용

### 2.1 아키텍처 및 데이터 흐름 (Baseline)

- **SSOT (Single Source of Truth)**: `data/ssot_sorted.csv`(정렬/라벨)와 `data/ssot_ordered.csv`(순서/피처) 2계층을 분리 배치하고, `exclude_rounds.csv`, `ssot_conflicts.csv`를 포함한 **계약 파일 세트**를 확정했습니다.
- **레거시 청산**: 구형 폴더/파일을 `99_Warehouse_Legacy`로 격리하여 운영 베이스라인의 오염을 차단했습니다.
- **No-Generation 원칙(아키텍처 계약)**: 본 단계는 “분석/리포트/후보 산출” 기반을 위한 스캐폴딩이며, 조합 생성은 오너 명령 기반의 별도 단계로 분리 운용합니다(후속 단계에서 구현/연결).

### 2.2 코어 모듈 구현 범위 (현재 단계)

- `constants.py`: 전역 상수/경로 정의  
- `ssot_loader.py`: SSOT 로드 및 제외 처리 로직  
- `features_sorted.py` / `features_ordered.py`: 기초 피처 추출기 **초안**  
- `backtest.py`: Recall@K 평가 로직 **구현(평가 레이어의 기반)**  

### 2.3 엔진 모듈 상태 (현재 단계)

- 계약된 엔진 파일(예: `nt4.py`, `nt5.py`, `al1.py` 등) **모듈 생성 + Docstring/스켈레톤 함수**까지 완료
- ⚠️ 실제 알고리즘은 다음 단계에서 rules/레거시 기반으로 채워야 함

> 참고: NT-SEQ는 아키텍처 문서에서 **Inactive(폐기)** 로 분류되며, 순서 기반 분석 역량은 AL 계열(예: AL1/AL2/ALX)로 흡수/운용합니다.

### 2.4 파이프라인 스크립트 (현재 단계)

- `scripts/run_round_pipeline.py`: SSOT 로드 → 엔진 순차 실행 → 산출물 저장(Artifacts) 흐름의 **골격 구현**

### 2.5 평가/Ω/생성/QA 자동화 (후속 단계로 이관)

본 v2.0 베이스라인 단계에서는 **평가 레이어(Recall@K) 기반(backtest.py)** 까지 확정했습니다.  
다만 아래 항목들은 “운영 자동화”로 가기 위한 **다음 단계(Implementation Sprint)** 로 분리합니다.

- (예정) 엔진별 TopK 산출 자동화 + Recall@20(전체/최근10/20/30) 리포트화
- (예정) Ω 가중치 업데이트(softmax, K_eval=20 기반) 및 후보풀(K_pool=22) 산출
- (예정) (오너 명령 시에만) 50조합 생성 + NT-DPP 전역 중복캡(공유≤2) QA
- (예정) 당첨번호 입력 시 채점/학습/다음 회차 가중 갱신까지의 운영 오케스트레이션

**[생성 제어 계약]**: 조합 생성(50조합)은 본 단계 범위 밖이며, 시스템은 Candidate Pool 산출까지만 수행한다. 조합 생성은 오너의 명시적 명령(예: GENERATE_50) 없이는 절대 실행되지 않는다.

즉, 현재 문서는 “운영 자동화 완료”가 아니라, **운영 자동화가 가능한 구조적 기반이 준비 완료**된 상태입니다.

---

## 3. 파일 구조 및 산출물

```text
C:\Users\a\OneDrive\바탕 화면\로또분석
│
├── data/                       # [SSOT] 정제 데이터
│   ├── ssot_ordered.csv
│   ├── ssot_sorted.csv
│   └── ...
│
├── nt_lotto/                   # [Package] 핵심 로직
│   ├── nt_core/                # 공통 기능 (Loader, constants, Features)
│   ├── nt_engines/             # 14개 엔진 모듈 (nt4.py, al1.py ...)
│   └── scripts/                # 실행 파이프라인
│
├── 03_Global_Analysis_Archive/ # [Reports] 보고서 저장소
│   ├── Architecture_Reports/   # 아키텍처 문서
│   └── NT_WORK_COMPLETION_REPORT.md
│
└── 99_Warehouse_Legacy/        # [Archive] 구 버전 백업
```

## 4. 결론

NT Project v2.0은 현재 **운영 자동화의 ‘기반(Baseline/Scaffolding)’이 완료된 상태**입니다.  
다음 단계는 (1) **SSOT 데이터 무결성 검증**, (2) **엔진 로직 이식(스켈레톤 → 실제 알고리즘)**, (3) **단위 테스트 수행**을 통해 “진짜 Operational”로 승격하는 것입니다.

본 보고서는 ‘운영 완료’가 아니라 ‘운영 가능 구조의 기반 확립’ 단계이며, 엔진별 점수식/TopK/Recall@20/Ω 가중치/후보풀/50조합 생성/QA는 **다음 단계 구현 항목**으로 정의합니다.
