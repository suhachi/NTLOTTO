# NT Project v2.0 - 개발자 및 운영자 가이드 (Scaffolding Phase)

**버전**: 2.0 (Baseline Established)
**작성일**: 2026.02.16
**상태**: 엔진 로직 구현 대기 중 (Ready for Implementation)

---

## 1. 프로젝트 개요

본 프로젝트는 로또 번호 분석 및 생성을 위한 **확장 가능한 모듈형 파이프라인**입니다.  
현재 단계는 **'뼈대(Scaffolding)'**가 완성된 상태로, 데이터 로드 -> 분석 -> 엔진 실행 -> 결과 저장의 파이프라인 구조는 잡혀 있으나, 각 엔진(`NT4`, `AL1` 등)의 내부 로직은 비어 있거나 기초적인 스텁(Stub) 상태입니다.

이 가이드는 **(1) 엔진 로직을 구현하는 개발자**와 **(2) 향후 시스템을 운영할 오너**를 위해 작성되었습니다.

---

## 2. 폴더 구조 및 역할

```text
nt_lotto/
├── nt_core/              # 공통 라이브러리 (절대 수정 금지 원칙)
│   ├── ssot_loader.py    # 데이터 로더 (SSOT + 제외회차 처리)
│   ├── constants.py      # 전역 상수 (K, Pool 크기 등)
│   └── ...
├── nt_engines/           # [개발 핵심] 개별 분석 엔진
│   ├── nt4.py            # (예) 빈도 기반 엔진
│   ├── al1.py            # (예) 시계열 예측 엔진
│   └── ...
└── scripts/              # 실행 스크립트
    └── run_round_pipeline.py  # 메인 실행 파이프라인
```

---

## 3. 개발자 가이드: 엔진 로직 구현 방법

### 단계 1: 엔진 파일 열기
구현하고자 하는 엔진의 파일을 엽니다. (예: `nt_lotto/nt_engines/nt4.py`)

### 단계 2: `analyze` 함수 구현
각 엔진 파일에는 표준화된 `analyze(df)` 함수가 정의되어 있습니다. 이 함수 안에 실제 분석 로직을 작성하세요.

**작성 예시 (`nt4.py`):**
```python
def analyze(df_history):
    """
    NT4: 전체 회차 빈도 분석 엔진
    Input: df_history (과거 당첨 데이터 DataFrame)
    Output: 추천 번호 리스트 (Top 20)
    """
    # 1. 번호별 빈도 계산
    freq = df_history.iloc[:, 2:8].stack().value_counts()
    
    # 2. 상위 20개 추출
    top20 = freq.head(20).index.tolist()
    
    return top20  # 반드시 리스트 형태 반환
```

### 단계 3: 파이프라인 테스트
로직 구현 후, 파이프라인 스크립트를 실행하여 오류 없이 작동하는지 확인합니다.

```powershell
# 프로젝트 루트에서 실행
python -m nt_lotto.scripts.run_round_pipeline
```
*성공 시: `[SUCCESS] Output saved to .../NT_Result.json` 메시지 출력*

---

## 4. 운영자 가이드: 매주 루틴 (Future Operations)

모든 엔진 구현이 완료된 후(Implementation Sprint 종료 후), 매주 토요일 추첨 직후 다음 절차를 따릅니다.

### 1단계: 데이터 업데이트 (SSOT)
1.  **`data/ssot_sorted.csv`**: 이번 주 당첨번호를 맨 아래 행에 추가합니다.
2.  **`data/ssot_ordered.csv`**: 추첨 순서대로 번호를 추가합니다.

### 2단계: 파이프라인 실행
```powershell
python -m nt_lotto.scripts.run_round_pipeline --target [다음회차]
```
*   이 명령은 저장된 SSOT 데이터를 읽어와, 구현된 모든 엔진을 가동하고 다음 회차 예측 결과를 생성합니다.

### 3단계: (선택) 조합 생성
*   `--owner_command "GENERATE_50"` 옵션이 있을 때만 최종 50게임 조합을 생성합니다. (오너 승인 필수)

---

## 5. 주의사항 및 제약 (Contract)

1.  **SSOT 무결성**: `data/` 폴더 내의 CSV 파일은 절대 임의로 삭제하거나 형식을 변경해서는 안 됩니다.
2.  **결정론적 결과**: 모든 엔진은 랜덤 함수(`random`, `np.random`) 사용이 금지됩니다. 동일한 입력에는 항상 동일한 예측을 내놓아야 합니다.
3.  **제외 회차**: 기계 결함 등으로 신뢰할 수 없는 회차는 `data/exclude_rounds.csv`에 번호를 추가하여 분석에서 제외합니다.

---
**문의**: System Architect Team
