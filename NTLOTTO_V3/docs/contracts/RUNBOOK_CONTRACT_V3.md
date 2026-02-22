# RUNBOOK_CONTRACT_V3 (강제 계약)

## 1) 엔진 키(SSOT)
허용 키: NT4, NT5, NTO, NT-Ω, NT-VPA-1, NT-LL, NT-PAT
그 외 키 등장 시 FAIL.

## 2) 전략 입력 계약
- 입력 문자열은 "엔진키 정수" 쌍의 리스트로 해석한다.
- 합계 quota는 M과 정확히 같아야 한다. 다르면 FAIL.
- 누락 엔진은 quota=0으로 간주(명시 권장).

## 3) 리포트 계약(형식)
- WHY_Long/WHY_Short/ENG_* 리포트는 고정 헤더와 고정 섹션을 포함해야 한다.
- 섹션 누락/이름 변경 시 FAIL.

## 4) 예측(조합 생성) 계약
- Actual==Quota 강제.
- RandomFallback은 0이 목표. 허용 상한 fallback_max(기본 5). 초과하면 FAIL.
- 헌법 위반 시 FAIL.

## 5) 채점 계약
- 정답 판정은 ssot_sorted 기반(정렬 6개+bonus).
- 입력은 추첨순서로 받되, 판정은 정렬 SSOT로만 수행.
