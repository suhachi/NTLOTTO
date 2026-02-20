# NT Project System Architecture Report v2.0
**문서 번호**: NT-ARCH-RPT-20260215-001
**작성 일자**: 2026년 2월 15일
**작성자**: NT System Architect (Copilot)
**상태**: **Approved (Active)**

---

## 1. 아키텍처 개요 (Executive Summary)

본 문서는 NT 프로젝트가 기존의 단일 스크립트 기반 방식에서 **"엔진 중심(Engine-Centric)"**의 모듈형 아키텍처로 진화했음을 선언하고, 그 상세 구조를 정의합니다.

### 1.1 핵심 변화 (Key Changes)
- **모듈화 (Modularization)**: 모든 예측 로직은 독립 엔진 모듈로 분리되며, 각 엔진은 자신의 규칙(`rules.md`)과 구현(`engine_*.py`)을 가진다.  
  단, **입력 데이터는 오직 중앙 SSOT(data/ssot_sorted.csv, data/ssot_ordered.csv)만 사용**하며, 엔진은 SSOT를 복제/보관/수정하지 않는다.  
  엔진별 산출물(리포트/점수/TopK)은 `03_History_Archive/Analysis_Reports/{round}/` 하위에 **멱등(Overwrite-safe) 방식으로 저장**한다.
- **데이터 흐름의 단방향성 (Unidirectional Data Flow)**: `00_Data_Center` (입력) → `NT_Engines` (개별 처리) → `NT_Omega` (통합) → `NTO` (최적화)의 명확한 흐름을 갖습니다.
- **SSOT 원칙 강화**: 모든 엔진은 동일한 정제 데이터(`ssot_ordered.csv`, `ssot_sorted.csv`)만을 참조하여 데이터 불일치를 원천 차단합니다.

---

## 2. 전체 시스템 아키텍처 (Global System Architecture)

시스템은 크게 **데이터 계층, 엔진 계층, 메타 계층**으로 구분됩니다.

```mermaid
flowchart TD
    A[MD Data Files] --> B[scripts/import_md.py]
    B --> C[data/ssot_sorted.csv (LABEL/판정 SSOT)]
    B --> D[data/ssot_ordered.csv (FEATURE/순서 SSOT)]
    B --> X[data/ssot_conflicts.csv]
    B --> Y[data/exclude_rounds.csv]

    C --> E[Feature Extraction: Sorted 기반]
    D --> F[Feature Extraction: Ordered 기반(AL 전용)]
    Y --> E
    Y --> F

    E --> G[Engine Scoring (14 engines)]
    F --> G

    G --> H[Engine Reports + TopK(K_eval=20)]
    H --> O[Omega Aggregator (NT-Ω: K_pool=22 후보풀)]
    O --> P[Candidate Pool Only (No Generation)]

    P --> Q{Owner explicit command?}
    Q -- No --> R[STOP: 분석/학습/리포트 저장만]
    Q -- Yes --> S[Generate 50-combo portfolio]
    S --> T[QA: NT-DPP + global overlap caps]
    T --> U[Archive: MD/CSV artifacts]
```

---

## 3. NT 엔진 아키텍처 (NT Engine Architecture)

각 "엔진(Engine)"은 하나의 독립된 **마이크로 서비스**처럼 설계되었습니다. 모든 엔진 폴더는 동일한 표준 구조를 따릅니다.

### 3.1 표준 디렉토리 구조 (Standard Layout)

```text
nt_lotto/
├── nt_core/
│   ├── constants.py              # SSOT 경로/고정 상수(K_eval=20, K_pool=22)
│   ├── ssot_loader.py            # exclude_rounds 포함 로더(멱등)
│   ├── features_sorted.py        # sorted 기반 피처
│   ├── features_ordered.py       # ordered 기반 피처(AL 전용)
│   └── backtest.py               # walk-forward + Recall@K 평가
├── nt_engines/
│   ├── nt4.py
│   ├── nt5.py
│   ├── nto.py
│   ├── nt_omega.py
│   ├── nt_ll.py
│   ├── vpa.py
│   ├── nt_vpa_1.py
│   ├── al1.py
│   ├── al2.py
│   ├── alx.py
│   ├── nt_exp.py
│   ├── nt_dpp.py
│   ├── nt_hce.py
│   └── nt_pat.py
├── scripts/
│   ├── import_md.py
│   └── run_round_pipeline.py
├── data/
│   ├── ssot_sorted.csv
│   ├── ssot_ordered.csv
│   ├── ssot_conflicts.csv
│   └── exclude_rounds.csv
└── 03_History_Archive/
    └── Analysis_Reports/
        └── {round}/              # 엔진 리포트/TopK/Ω weights/후보풀 저장(멱등)
```

### 3.2 엔진 카탈로그(고정 14개) + 입력 SSOT 계약

> **운영 고정 엔진(14개)**:  
> NT4, NT-Ω, NT5, NTO, NT-LL, VPA, NT-VPA-1, AL1, AL2, ALX, NT-EXP, NT-DPP, NT-HCE, NT-PAT  
> ✅ 엔진 추가/삭제/개명 금지(Contract 개정 절차 없이 변경 불가)

| Engine | 목적/역할 | 입력 SSOT | 핵심 피처(요약) | 학습/산출물(고정) | Backtest KPI(고정) | Ω 업데이트 입력 |
|---|---|---|---|---|---|---|
| NT4 | 장기+최근 트렌드 기반 베이스 | sorted | freq_global, freq_recent_30, trend_30, macro-guards | TopK(20) 번호 리스트 + score.csv | Recall@20 (전체/최근10/20/30) | recall_total, recall_10/20/30 |
| NT5 | Hot/클러스터 기반(보수적 캘리브레이션) | sorted | Hot30/50/100, R5/R10, macro-penalty | TopK(20) 번호 + score.csv | Recall@20 슬라이스 | same |
| NTO | 통합 점수(엔진 점수 결합의 “독립 엔진”) | sorted 중심(+타 엔진 점수) | NT4/NT5/VPA/LL의 결합 스코어 | TopK(20) 번호 + score.csv | Recall@20 슬라이스 | same |
| NT-Ω | 메타 앙상블/포트폴리오(후보풀 생성) | sorted+engine outputs | 엔진별 TopK를 가중 결합, 후보풀 K_pool=22 | 후보풀(22) + Ω weights.json | Recall@20 기반 가중 갱신 | (엔진별 KPI) → softmax |
| NT-LL | 로컬(최근10~20) 보정항 | sorted | dev_local(20), under/over 보정 | 보정 score.csv | Recall@20 슬라이스 | same |
| VPA | Pair/Anchor(동반출현) 신호 | sorted | pair lift/PMI, anchor 확장 | TopK(20) 번호 + pair_matrix 요약 | Recall@20 슬라이스 | same |
| NT-VPA-1 | VPA 강신호만(임계치↑) | sorted | VPA의 상위 강신호 subset | TopK(20) 번호 | Recall@20 슬라이스 | same |
| AL1 | **순서 기반(슬롯/위치) 분석 전용** | ordered | slot dist(1~6구), band-by-slot | TopK(20) 번호 + slot_report | Recall@20 슬라이스 | (기본 0~ε) ※검증 통과 시만 |
| AL2 | **순서 기반(전이) 분석 전용** | ordered | band transition(5x5), smoothed Markov | TopK(20) 번호 + trans_report | Recall@20 슬라이스 | (기본 0~ε) ※검증 통과 시만 |
| ALX | **AL1+AL2 하이브리드(운영 엔진)** | ordered(+AL1/AL2) | AL1/AL2 점수 결합 | TopK(20) 번호 + alx_score | Recall@20 슬라이스 | 제한적 반영(게이트) |
| NT-EXP | 실험 슬롯(소량) | sorted | 특정 실험 피처(명시 필요) | TopK(20) + exp_notes | Recall@20 슬라이스 | 성과 없으면 가중 0 |
| NT-DPP | “세트 분산/중복 억제” QA 엔진 | set-level | overlap cap, jaccard, freq-cap | qa_report + violations | (KPI 아님: QA PASS/FAIL) | Ω 입력 아님(후처리) |
| NT-HCE | 끝수/클러스터 문샷(소량) | sorted | ending clusters, ending freq | TopK(20) + ending_report | Recall@20 슬라이스 | 성과 기반 미세 반영 |
| NT-PAT | 레짐/패턴 룰 기반 특화 | sorted(+ordered 요약 가능) | band vec, sum zscore, oe, runlen, templates | TopK(20) + pat_rules_hit | Recall@20 슬라이스 | 성과 기반 반영 |


> **중요(운영 원칙 고정)**
>
> 1. AL1/AL2는 “순서 데이터로 최고의 분석 리포트를 뽑는 모듈”이어야 하며, 무조건 가중치 상향이 아니라 검증 게이트 통과 시에만 Ω 반영합니다.  
> 2. “조합 생성”은 엔진이 아니라 오너의 명령으로만 수행됩니다(별도 Generate 단계).

---

## 4. 데이터 처리 파이프라인 (Processing Pipeline)

1. **Ingestion (수집)**:
   - 입력은 오직 `data/` 하위 SSOT 파일에서 로드한다.
     - `data/ssot_sorted.csv` (LABEL/판정 SSOT)
     - `data/ssot_ordered.csv` (FEATURE/순서 SSOT)
     - `data/exclude_rounds.csv` (학습/백테스트 제외 목록)
     - `data/ssot_conflicts.csv` (불일치 격리 로그)
2. **Analysis (개별 분석)**:
   - 각 엔진이 독립적으로 데이터를 분석하여 `03_History_Archive/`에 점수(Score) 또는 후보군(Candidates)을 저장.
3. **Integration (통합)**:
   - `NT-Ω`는 각 엔진의 **Backtest KPI(Recall@K_eval=20)** 를 입력으로 사용한다.
   - KPI는 **전체/최근10/최근20/최근30** 슬라이스를 모두 계산하며,
     Ω 가중치 업데이트는 이 KPI 벡터를 기반으로 수행한다.
   - (예) `kpi_i = [recall_total, recall_10, recall_20, recall_30]`
4. **Candidate Pool 산출(생성 아님)**:
   - 각 엔진은 **TopK(K_eval=20) 번호** 및 리포트를 산출한다.
   - `NT-Ω`는 엔진별 KPI(Recall@20 전체/최근10/20/30)를 입력으로 **가중치(softmax)를 갱신**하고, **K_pool=22 후보풀만 생성**한다.
   - ⚠️ 이 단계에서는 **조합(50조합) 생성 금지**: 오너의 명시적 “예측조합 생성” 지시가 있을 때만 별도 Generate 스텝을 실행한다.
5. **Quality Assurance (검수)**:
   - `NT-DPP`는 생성된 50조합에 대해 전역 규칙을 검사한다.
     - Hard: Pairwise Overlap Cap (|Ci ∩ Cj| ≤ 2)
     - Soft: Number Frequency Cap, Jaccard Cap
   - QA 결과는 **PASS/FAIL**로 출력하며,
     FAIL 시에는 **리젝 사유(조합ID/위반 규칙/증거)**를 기록하고 교체 후보를 요청한다.

---

## 5. 결론 (Conclusion)

이 구조는 **재현성(Reproducibility)**과 **무결성(Integrity)**을 최우선으로 합니다.  
따라서 **운영 엔진 목록은 14개로 고정**되며, 엔진 추가/삭제/개명은 **금지**합니다.

새 아이디어는 다음 원칙으로만 수용됩니다.
1. **R&D(연구) 모듈**로만 별도 구현(운영 파이프라인 미편입)  
2. Walk-forward + Recall@K(전체/최근10/20/30)에서 **기준선 대비 유의미한 uplift**가 확인될 때만  
3. **Contract 개정 절차**를 통해 운영 엔진으로 승격

즉, “쉽게 추가하는 확장성”이 아니라, **검증을 통과한 것만 운영에 들어오는 보수적 확장성**을 시스템 철학으로 채택합니다.

> **NT-SEQ 관련 메모**  
> 과거에 “NT-SEQ(순서 기반 단일 엔진)”을 신설하려는 시도가 있었으나, 운영 안정성을 위해 **운영 엔진으로는 채택하지 않는다.**  
> 대신 순서 기반 역량은 **AL1(슬롯 편향) / AL2(전이) / ALX(AL1+AL2 하이브리드)**의 3분리 체계로 고정한다.  
> 순서 데이터는 **분석력(리포트) 측면에서는 최고 수준으로 강화**하되, Ω 가중치 반영은 **검증 게이트를 통과한 경우에만 제한적으로 허용**한다.

<br>

※ 본 문서는 “아키텍처 계약(Contract)”이며, 실제 리포지토리 반영 여부는 커밋/파일 diff로만 판정한다.
