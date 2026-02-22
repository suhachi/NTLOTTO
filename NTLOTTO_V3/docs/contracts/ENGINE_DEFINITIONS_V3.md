# NTLOTTO V3 엔진 정의 계약서 (SSOT)

이 문서는 NTLOTTO V3 파이프라인에서 사용되는 분석 및 예측 엔진들의 역할과 제약 사항을 정의하는 단일 진실 공급원(SSOT)입니다.

## 1. 공통 정의
- **레이어 분리**: 분석(WHY) → 전략(선택) → 예측(조합)은 철저히 분리되며, 본 엔진들은 **후보풀(Candidate Pool) 도출 및 점수화(Scoring)**에만 관여합니다. 조합은 생성하지 않습니다.
- **SSOT 데이터**: 평가는 오직 `ssot_sorted.csv`로 진행되며, `ssot_ordered.csv`는 패턴 분석(추첨순서 등)의 피처로만 사용됩니다.

### ✅ 공통 인터페이스 반환값
- `score_map`: 1~45번 점수 딕셔너리(기본 0~1 스케일). **단, NT-PAT는 기본 hint_only로 score_map을 0(또는 매우 약하게) 둘 수 있습니다.**
- `candidate_pool`: 상위 후보 번호 리스트(TopK). **단, NT-PAT의 candidate_pool은 ‘힌트 후보(hint_pool)’ 성격입니다.**

### ✅ 엔진 키 표준(SSOT 고정)
본 프로젝트에서 사용하는 엔진 키는 아래 7개로 **고정**합니다(문서/코드/선택파일/리포트 전부 동일).
- NT4, NT5, NTO, NT-Ω, NT-VPA-1, NT-LL, NT-PAT

### ✅ 조합 생성(예측) 책임 분리
- **엔진(Engine)**: 점수화(score_map) 및 후보풀(candidate_pool/hint_pool) 산출만 담당하며 **조합을 직접 생성하지 않습니다.**
- **조합 생성(Predict Layer)**: `src/ntlotto/predict/`에서만 수행되며, **2중 잠금(환경변수 + CLI 플래그)**이 없으면 절대 실행되지 않습니다.

## 2. 엔진별 계약(Contract)

### NT4 (Baseline: Global Frequency + Recent Trend)
- **정의 및 역할**: 장기 빈도와 최근 트렌드의 안정축을 담당.
- **입력**: `ssot_sorted` (주), `ssot_ordered` (미사용)
- **출력**: `score_map(1..45)`, `candidate_pool(TopK; 기본 18~28)`
- **금지사항**: 최근성이나 핫 클러스터에 과도하게 편향되는 것을 금지하며 단독 올인은 권장하지 않음.
- **대표 지표**: 전체 회차 빈출도 및 최근 30회 트렌드.

### NT5 (Hot Cluster: Recent 5~10 Hot)
- **정의 및 역할**: 최근 5~10회차 이내의 Hot 번호 및 클러스터 타격.
- **입력**: `ssot_sorted`
- **출력**: `score_map`, `candidate_pool`
- **금지사항**: Cold 번호를 배제(0점 처리)하는 완전 배제 방식 금지 (가중치 차등만 허용).

### NTO (Meta Optimizer: Blend)
- **정의 및 역할**: 여러 엔진의 신호를 결합하는 통합(메타) 엔진.
- **입력**: `ssot_sorted`, 다른 엔진들의 `score_map`
- **출력**: `score_map`, `candidate_pool`
- **주의사항**: 다른 엔진을 흡수해 결과가 동일해지는 현상 방지(선택 레이어에서 비중 통제).

### NT-Ω (Recency + Diversity)
- **정의 및 역할**: 최근성(5~10회) 활용 및 분산/커버리지 경고.
- **입력**: `ssot_sorted`
- **출력**: `score_map`, `candidate_pool` (K_pool 기본 22~30)
- **주의사항**: NTO와 TopK가 과도하게 겹칠 경우 포트폴리오 다양성 감소 우려 (독립성 보장 필요).

### NT-VPA-1 (Vertical Pattern Anchor)
- **정의 및 역할**: 번호대, 연번, 끝수의 기하학적 형태/패턴 앵커 보조 전략.
- **입력**: `ssot_sorted`
- **출력**: `score_map`(약한 가중치), `candidate_pool`
- **주의사항**: 패턴 강제로 인한 기대값(EV) 훼손 방지를 위해 미세조정(보조)용으로만 사용.

### NT-LL (Local Deviation / Drift)
- **정의 및 역할**: 초단기 국소 변화량(Drift) 및 편차에 추종하는 흐름 반전 보정축.
- **입력**: `ssot_sorted`
- **출력**: `score_map`, `candidate_pool`
- **주의사항**: 노이즈 반응성이 높아 단독 주력 사용 금지 (보조 슬롯 전용).

### NT-PAT (Pattern Analyzer: Hint-only by default)
- **정의 및 역할**: 쌍(Pair), 간격, 전이 등의 패턴 탐지 및 누락(Coverage) 방지 보조 힌트.
- **입력**: `ssot_sorted` + `ssot_ordered` (전이 측정)
- **출력**: 보조용 `candidate_pool` (기본 점수 산출 제외 또는 0점 부과)
- **기본 계약**: `hint_only` (Coverage 힌트 제공 전용)
- **금지사항**: PAT 단독으로 메인 score를 지배하도록 설계 금지.
