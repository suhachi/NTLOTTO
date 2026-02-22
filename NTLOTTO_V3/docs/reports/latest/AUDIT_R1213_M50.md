# AUDIT_R1213_M50.md
**Conclusion:** FAIL

## Top Risks & Corrections
1. RandomFallback 비율: 해당 한도를 초과할 경우 전략 엔진 점유율 보강 필요.
2. EV 슬롯 제한: 공유 3개 조합 수가 너무 많으면 허용범위 초과 (FAIL시 수정: Jaccard 조정 등)


## Checklist
| Check ID | Status | Reason |
|----------|--------|--------|
| SSOT_INTEGRITY | PASS | Rows=606 |
| M_TARGET | PASS | Generated=50 |
| HARD_OVERLAP_4+ | PASS | 0 count |
| EV_SLOT_CAP | FAIL | Used=7 > 5 |
| FREQ_CAP | PASS | 8 <= 8 |
| FALLBACK_LIMIT | FAIL | 32 > 5 |
| ENGINE_STRATEGY | PASS | Strategy file present |

## Core Metrics (Recalculated)
- Max Overlap: 3
- Overlap >= 4 Count: 0
- EV Combo Count (Overlap=3 involved): 7
- Max Number Frequency: 8 / Cap: 8
- Max Jaccard Seen: 0.333
- RandomFallback Count: 32

## Engine Distribution (Actual)
- NTO: 5
- NT4: 4
- NT-LL: 4
- NT5: 2
- NT-Ω: 3
- RandomFallback: 32

## EV Combinations (Involved in overlap=3)
- [17, 26, 27, 35, 38, 39]
- [1, 3, 12, 23, 26, 39]
- [3, 16, 17, 23, 26, 27]
- [3, 6, 23, 26, 31, 38]
- [1, 3, 6, 16, 26, 35]
- [2, 3, 8, 23, 26, 40]
- [1, 3, 4, 6, 8, 10]