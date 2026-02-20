# NT Project v2.0 설정 가이드

## 기본 환경 설정
- **기본 언어**: 한국어 (모든 문서, 주석, 보고서 및 에이전트 소통)
- **주요 프레임워크**: Python 3.13+, pandas, numpy, pytest
- **데이터 표준 (SSOT)**:
    - `data/ssot_sorted.csv`: 번호 정렬 데이터 (기본 입력)
    - `data/ssot_ordered.csv`: 추첨 순서 데이터 (AL 엔진 전용)
    - `data/exclude_rounds.csv`: 제외 회차 목록

## 에이전트 행동 지침
1. 사용자와의 모든 소통은 한국어로 진행한다.
2. 모든 보고서(walkthrough), 계획서(implementation_plan), 작업 목록(task.md)은 한국어로 작성한다.
3. 코드 내 주요 로직 설명 및 독스트링(docstring)도 가급적 한국어를 병행하거나 한국어로 작성한다.
