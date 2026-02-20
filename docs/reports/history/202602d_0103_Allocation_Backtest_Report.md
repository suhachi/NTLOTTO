# Allocation Backtest Report (K=20, N=100)
Generated At: 202602d_0103
| Constraint | Status |
| :--- | :---: |
| Look-ahead | **PASS** (Strict round limitation) |
| Determinism | **PASS** |
| SSOT Conformity | **PASS** |

## Ω vs NTO Overlap Analysis
- **Jaccard@20 Mean**: 1.000 (Std: 0.000)
- **⚠️ WARNING**: Jaccard mean > 0.70. Ω is too similar to NTO; diversity may be compromised.

## Metric Summary (Overall)
| Plan | Mean Recall | Std Recall | Mean Bonus Hit | Sharpe-like |
| :--- | :---: | :---: | :---: | :---: |
| Conservative | 2.610 | 1.094 | 0.450 | 2.385 |
| Balanced | 2.610 | 1.094 | 0.460 | 2.385 |
| Aggressive | 2.670 | 1.096 | 0.460 | 2.436 |

## Fold-by-Fold Recall (Means)
| Plan | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Conservative | 2.40 | 2.85 | 2.40 | 2.60 | 2.80 |
| Balanced | 2.40 | 2.75 | 2.50 | 2.60 | 2.80 |
| Aggressive | 2.50 | 2.85 | 2.40 | 2.80 | 2.80 |

## Conclusion
**Aggressive 승(Win)** - Recall, BonusHit, 안정성 기준에서 가장 우수합니다.