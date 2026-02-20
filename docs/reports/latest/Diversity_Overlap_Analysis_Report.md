# NT Project v2.0: 중복 방지(Diversity & Overlap Control) 링가드 분석 보고서
**작성일시**: 2026-02-21
**분석범위**: NT Project v2.0 코어 패키지 (`nt_lotto/nt_core/`, `run_portfolio_pipeline.py` 내부 등) 전체 스캔

## 1. 개요
NT Project v2.0 내에는 엔진이 생성하는 조합들이 "동일 확률 영역"에 몰리거나 과도한 교집합을 형성하지 않도록 **포트폴리오 레벨의 중복 방지(Diversity) 장치**가 선제적으로 구축되어 있습니다. 
사용자님의 요청에 따라 현재 프로젝트 코드망 내에 정의된 중복 방지 규칙과 해당 수치 임계값을 분석했습니다.

## 2. 핵심 중복 방지 장치 현황

### 2.1. 조합 내부 중복 방지 (Set / Unique Check)
- **위치**: `nt_lotto/nt_core/integrity.py` 및 엔진 데이터 추출부
- **내용**: 
  - 각 추첨 라운드 번호 배열은 `len(set(numbers)) == 6` 통과 검사를 거칩니다.
  - 하나의 조합(1~45) 내에 동일한 번호를 중복 포함하지 않도록 보장합니다.

### 2.2. 포트폴리오 간 상호 교점 제한 (Hard Limits)
- **위치**: `nt_lotto/nt_core/schemas.py`, `nt_lotto/nt_core/generate.py`, `run_portfolio_pipeline.py`
- **구현 상태**: **구현/탑재 완료** (조합 생성 모듈에 적용 가능)
- **주요 파라미터**:
  - `max_overlap`: **2** 
    > _해설_: 임의의 두 가지 6자리 조합(예: A조합, B조합)을 생성할 때, 서로 같은 번호가 최대 **2개까지만** 겹치도록 제한합니다. 3개 이상 숫자가 겹치는 조합은 "다양성 위반(`overlap_violations`)"으로 폐기됩니다.
  
### 2.3. 포트폴리오 간 자카드 스코어 제한 (Soft/Distribution Limits)
- **위치**: `run_portfolio_pipeline.py` (Line 114)
- **적용 수치**: `max_jaccard: 0.30`
- **현 상태**:
  - 교집합 개수(Overlap)뿐 아니라 Jaccard Index(합집합 대비 교집합 비율)를 계산하여, 조합 간의 유사도가 30%를 넘지 않도록 억제하는 페널티 장치가 준비되어 있습니다.

### 2.4. 평가 백테스트 단계에서의 검증 (Top20 점검)
- **위치**: `nt_lotto/scripts/07_backtest_allocation.py`
- **현 상태**: Sprint 4에서 도입된 로직에 따라 NT-Omega와 NTO 간의 **Jaccard@20 Overlap** 평균을 백테스트마다 추적합니다.
- **가드라인**: 두 엔진 간의 번호 일치도가 `0.70 (70%)`을 초과할 경우 `⚠️ WARNING: Ω is too similar to NTO; diversity may be compromised.` 경고가 발동하여, 최상위 후보군 번호 중복(쏠림) 현상을 방어합니다.

## 3. 결론 및 향후 활용
현재 NT Project v2.0 코어에는 **조합(Tuple) 수준의 엄격한 중복 차단(Max Overlap 2개 이하)**과 **후보 풀(Pool) 수준의 유사도 경고(Jaccard 모니터링)** 장치가 체계적으로 모듈화되어 있습니다.
이후로 포트폴리오(실제 구매될 5~6개 조합) 생성 태스크를 가동하게 될 때, 이 `overlap` 필터들이 자동으로 적용되어 "불필요하게 유사한 조합 생성을 차단"하고 "비용 대비 타격 커버리지(Diversity)"를 최대로 확장하게 됩니다.
