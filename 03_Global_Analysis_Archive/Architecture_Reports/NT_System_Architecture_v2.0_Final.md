# NT Project v2.0 시스템 구조 및 아키텍처 정밀 보고서 (Final)

**문서 번호**: NT-ARCH-20260216-FINAL  
**작성 일자**: 2026-02-16  
**작성자**: NT System Architect (Copilot)  
**상태**: **운영 기반 확립 (Baseline Established, Scaffolding Ready)**  

---

## 1. 서문
본 문서는 NT Project v2.0의 **최종 확정된 폴더 구조, 파일 체계, 시스템 흐름(Architecture)** 을 기술합니다.  
본 프로젝트는 **SSOT(Single Source of Truth)** 원칙을 엄격하게 준수하며, 운영 자동화와 분석의 재현성을 보장하기 위해 모든 데이터와 로직을 모듈 단위로 분리하였습니다.  
현재 상태는 **"운영 스캐폴딩(Baseline) 구축 완료"** 단계이며, 각 예측 엔진의 핵심 알고리즘(Logic Injection)을 기다리는 상태입니다.

---

## 2. 시스템 아키텍처 (System Architecture)

### 2.1 Core Philosophy
1.  **SSOT 기반 데이터 관리**: 모든 분석의 기준은 `data/ssot_*.csv` 파일이며, 마크다운(MD) 원본에서 파싱되어 검증된 데이터만 사용합니다.
2.  **Engine Independence**: 14개의 예측 엔진은 상호 독립적이며, 표준 입출력(Input: History, Output: Top-K)을 통해 파이프라인과 소통합니다.
3.  **Phase Separation**: 과거 데이터 분석(Backfill)과 미래 예측(Prediction)을 엄격히 분리하여, **Look-ahead Bias(미래 참조 오류)** 를 원천 차단합니다.
4.  **Meta-Ensemble (Ω)**: 특정 엔진에 의존하지 않고, 성과(Recall@20)가 입증된 엔진에 가중치를 부여하는 적응형(Adaptive) 시스템을 지향합니다.

### 2.2 운영 파이프라인 (Operational Flow)

전체 시스템은 **Step A ~ F**의 단계적 흐름으로 구성됩니다.

| Step | 명칭 | 설명 | 담당 스크립트 |
|:---:|:---|:---|:---|
| **A** | **Import** | MD 원본을 읽어 SSOT(Sorted/Ordered) 갱신 | `scripts/import_md.py` |
| **B** | **Score** | 이전 회차 포트폴리오(50게임) 채점 | `scripts/run_round_pipeline.py` |
| **C** | **Analysis** | R회차 엔진 실행(사후분석) 및 KPI(Recall) 갱신 | `scripts/run_round_pipeline.py` -> `run_engines.py` |
| **D** | **Integrate** | 엔진 성과 기반 Ω 가중치(Softmax) 업데이트 | `scripts/run_round_pipeline.py` |
| **E** | **Predict** | (Optional) R+1회차 미래 예측 및 후보풀 생성 | `scripts/run_round_pipeline.py --mode next` |
| **F** | **Generate** | (Owner Only) 최종 50조합 생성 및 QA | `scripts/run_portfolio_pipeline.py` |

---

## 3. 상세 폴더 및 파일 구조 (Directory Structure)

프로젝트 루트 (`c:\Users\a\OneDrive\바탕 화면\로또분석`) 기준입니다.

### 3.1 `data/` (SSOT 데이터 레이어)
가장 중요한 데이터 원천입니다. 이 파일들이 없거나 오염되면 시스템은 정지합니다.

-   **`ssot_sorted.csv`**: (라벨) 오름차순 정렬된 당첨번호. 적중 판정(채점)에 사용.
-   **`ssot_ordered.csv`**: (피처) 추첨 순서대로 기록된 당첨번호. AL 엔진 등 순서기반 분석에 사용.
-   **`ssot_conflicts.csv`**: 데이터 정합성 충돌 로그.
-   **`exclude_rounds.csv`**: 분석에서 제외할 회차(기계적 오류, 이상치 등) 정의.

### 3.2 `nt_lotto/` (애플리케이션 패키지)
시스템의 모든 로직이 담긴 파이썬 패키지입니다.

#### 3.2.1 `nt_lotto/scripts/` (실행 파이프라인)
-   **`import_md.py`**: Step A 담당. 마크다운 데이터를 파싱하여 SSOT CSV로 변환.
-   **`run_round_pipeline.py`**: **[Main Orchestrator]** Step B, C, D, E를 관장. 엔진 실행, KPI 갱신, 가중치 산출 등을 순차 수행.
-   **`run_engines.py`**: 14개 엔진을 일괄 실행하여 Top-K 번호를 산출. Orchestrator에 의해 호출됨.
-   **`run_portfolio_pipeline.py`**: Step F 담당. 오너 승인 시에만, 후보풀에서 50조합을 생성하고 배합 규칙(QA)을 검사.

#### 3.2.2 `nt_lotto/nt_core/` (공통 라이브러리)
-   `constants.py`: 경로, 상수(K_EVAL, K_POOL 등) 정의.
-   `ssot_loader.py`: SSOT 데이터를 로드하고 필터링(Exclude)하는 모듈.
-   `kpi.py`: Recall@20 계산, 엔진 성과 기록 업데이트 로직.
-   `scoring.py`: 사용자가 구매한 포트폴리오(50게임)의 등수 채점 로직.
-   `omega.py`: Top-K와 KPI를 결합하여 Softmax 가중치를 계산하고 후보풀을 병합하는 로직.

#### 3.2.3 `nt_lotto/nt_engines/` (예측 엔진)
현재 14개 엔진의 스캐폴딩(Stub)이 존재합니다. 향후 각 파일의 `analyze()` 함수에 고유 알고리즘이 구현되어야 합니다.
-   `nt4.py`, `nt5.py`: 전통적 빈도/패턴 엔진.
-   `nt_omega.py`: 메타 분석 엔진.
-   `al1.py`, `al2.py`, `alx.py`: 딥러닝/시퀀스(LSTM 등) 기반 엔진.
-   `vpa.py`, `nt_dpp.py`: 벡터 패턴 및 다양성(DPP) 엔진.
-   (그 외 nto, nt_ll, nt_exp, nt_hce, nt_pat 등 총 14종)

### 3.3 `03_Global_Analysis_Archive/` (운영 산출물 저장소)
모든 분석 결과물이 저장되는 아카이브입니다.

-   **`Rounds/<RoundNumber>/`**: 해당 회차의 채점 결과, 요약 MD 리포트.
-   **`KPI/`**:
    -   `engine_kpi.csv`: 엔진별 현재 성능 지표.
    -   `engine_history_topk.json`: 엔진별 과거 예측 히스토리(KPI 산출용).
    -   `omega_weights_current.json`: 최신 Ω 가중치.
-   **`Omega_Pools/<RoundNumber>/`**:
    -   `engine_topk_K20.csv`: 엔진들이 뱉어낸 Top-20 예측.
    -   `omega_pool_K22.csv`: 가중치로 병합된 최종 후보 번호 22개.
-   **`Portfolios/<RoundNumber>/`**:
    -   `portfolio_50.csv`: 최종 생성된 50게임 (Step F 산출물).
-   **`NT_WORK_COMPLETION_REPORT_FINAL.md`**: 프로젝트 완료 현황 보고서 (SSOT 정합).

### 3.4 `99_Warehouse_Legacy/` (레거시 창고)
-   v1.0 시절의 이전 코드, 문서, 데이터를 격리 보관.

---

## 4. 운영 프로세스 가이드

### 4.1 기본 운영 (Weekly Routine)
1.  매주 토요일 추첨 후, 당첨번호를 마크다운(MD)에 기록.
2.  `python -m nt_lotto.scripts.import_md` 실행 (데이터 동기화).
3.  `python -m nt_lotto.scripts.run_round_pipeline --round <R>` 실행 (R회차 마감/평가).
4.  `python -m nt_lotto.scripts.run_round_pipeline --round <R> --mode next` 실행 (R+1회차 예상).

### 4.2 생성 운영 (On Demand)
1.  오너가 생성을 결정하면,
2.  `python -m nt_lotto.scripts.run_portfolio_pipeline --target <R+1> --owner_command "GENERATE_50"` 실행.
3.  생성된 `portfolio_50.csv` 확인.

---

## 5. 아키텍처 상태 요약 (System Health)

-   **SSOT Layer**: ✅ 구축 완료 (Import Script 동작)
-   **Engine Layer**: 🚧 스캐폴딩 완료 (로직 구현 대기)
-   **Pipeline Layer**: ✅ 오케스트레이션 로직 구현 완료 (`run_round_pipeline.py`)
-   **Logic State**: 
    -   Scoring/KPI/Omega 로직: ✅ 구현 완료
    -   Predictive Algorithms: ⬜ 미구현 (Stub 상태)

이 구조는 확장성(Scalability)과 관리 용이성(Maintainability)을 최우선으로 설계되었으며, 향후 엔진 로직이 추가되어도 파이프라인 구조는 변경 없이 유지됩니다.
