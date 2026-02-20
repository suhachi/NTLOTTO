# [시스템 구조 보고서] NT 프로젝트 디렉토리 및 아키텍처 (New Standard)

**문서 번호**: NT-ARCH-20260215-002
**작성 일자**: 2026년 2월 15일
**작성자**: NT System Architect (Copilot)
**상태**: **Approved (Active)**

---

## 1. 최상위 디렉토리 구조 (Top-Level Structure)

본 프로젝트는 **"엔진 중심(Engine-Centric)"** 아키텍처로 개편되었습니다. 모든 예측 로직은 `NT_Engines` 하위의 독립된 폴더에서 관리됩니다.

```text
C:\Users\a\OneDrive\바탕 화면\로또분석
│
├── 00_Data_Center/             # [SSOT] 정제된 데이터의 단일 진실 공급원
│   ├── ssot_ordered.csv        # 순서가 보존된 추첨 데이터
│   ├── ssot_sorted.csv         # 정렬된 추첨 데이터
│   └── raw_history/            # 원천 데이터 아카이브
│
├── NT_Engines/                 # [Core] 신규 예측 엔진 집합 (각 폴더가 하나의 모듈)
│   ├── NT4_Standard/           # 기본 통계 및 추세 분석 (Mean Reversion)
│   ├── NT5_Cluster/            # 군집 및 히트맵 분석 (Hot/Cold)
│   ├── NT_Omega_Integration/   # [Meta] 앙상블 및 가중치 통합 엔진
│   ├── NTO_Optimizer/          # [Meta] 조합 최적화 및 포트폴리오 구성
│   ├── NT_LL_Linear/           # 국소 선형 보정 (Local Linear Correction)
│   ├── NT_VPA_Pattern/         # 수직 패턴 및 구조 분석 (Vertical Pattern Anchor)
│   ├── AL_Adaptive_Series/     # 적응형 학습 시리즈 (Bayesian/Markov)
│   ├── NT_EXP_Exploration/     # [Exp] 미출현/희귀 조합 탐색
│   ├── NT_DPP_Diversity/       # [QA] 다양성 기반 조합 선별 (Determinantal Point Process)
│   ├── NT_HCE_Ending/          # [Exp] 끝수 집중 전략 (High Cluster Ending)
│   ├── NT_PAT_PatternMatch/    # 패턴 매칭 및 필터링
│   └── NT_SEQ_Sequence/        # [Inactive] 순서 기반 분석 (유의성 없음)
│
├── 03_Global_Analysis_Archive/ # [Report] 전체 분석 리포트 보관소
│
├── 99_Warehouse_Legacy/        # [Archive] 구 버전 코드 및 데이터 (격리됨)
│   ├── 01_Prediction_Engines_Legacy/
│   ├── nt_lotto_legacy/
│   ├── nt_reports_legacy/
│   └── nt_vnext_legacy/
│
├── nt_lotto/                   # [Deprecated] 구 패키지 구조 (이관 예정/Locked)
├── nt_reports/                 # [Deprecated] 구 리포트 패키지 (이관 예정/Locked)
│
├── PROJECT_CONSTITUTION.md     # 프로젝트 대전제 및 헌법
└── PROJECT_STRUCTURE.md        # 본 문서
```

## 2. 엔진별 표준 구조 (Standard Engine Layout)

각 `NT_Engines` 하위 폴더는 다음과 같은 표준 구조를 따릅니다:

```text
NT_Engines/Engine_Name/
├── rules.md                    # [Definition] 해당 엔진의 수학적 공식 및 논리 정의
├── script.py (예정)            # [Implementation] 파이썬 실행 코드
├── analysis_data/              # [Output] 해당 엔진이 생성한 분석 데이터
│   ├── result.json
│   └── debug_log.txt
└── tests/ (옵션)               # 단위 테스트
```

## 3. 데이터 흐름 (Data Flow)

1. **Input**: 모든 엔진은 `00_Data_Center`의 `ssot_*.csv` 파일을 읽습니다.
2. **Process**: `script.py`가 `rules.md`의 로직을 수행합니다.
3. **Output**: 결과는 각 폴더의 `analysis_data/`에 저장됩니다.
4. **Integration**: `NT_Omega_Integration` 엔진이 각 엔진의 출력을 취합하여 최종 조합을 생성합니다.

---
**변경 이력**:
- 2026-02-15: `01_Prediction_Engines` 등 레거시 폴더를 `99_Warehouse_Legacy`로 이동 및 격리. `NT_Engines` 표준 구조 확립.
