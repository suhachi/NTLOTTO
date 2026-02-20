# Allocation Backtest Report (K=20, N=100)
Generated At: 202602d_0111
| Constraint | Status |
| :--- | :---: |
| Look-ahead | **PASS** (Strict round limitation) |
| Determinism | **PASS** |
| SSOT Conformity | **PASS** |

## Ω vs NTO Overlap Analysis
- **Jaccard@20 Mean**: 0.940 (Std: 0.059)
- **⚠️ WARNING**: Jaccard mean > 0.70. Ω is too similar to NTO; diversity may be compromised.

## Metric Summary (Overall)
| Plan | Mean Recall | Std Recall | Mean Bonus Hit | Sharpe-like |
| :--- | :---: | :---: | :---: | :---: |
| Conservative | 2.640 | 1.118 | 0.440 | 2.361 |
| Balanced | 2.630 | 1.101 | 0.440 | 2.388 |
| Aggressive | 2.690 | 1.102 | 0.450 | 2.442 |

## Fold-by-Fold Recall (Means)
| Plan | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Conservative | 2.45 | 2.75 | 2.40 | 2.75 | 2.85 |
| Balanced | 2.40 | 2.70 | 2.55 | 2.65 | 2.85 |
| Aggressive | 2.50 | 2.95 | 2.45 | 2.75 | 2.80 |

## Conclusion
**Aggressive 승(Win)** - Recall, BonusHit, 안정성 기준에서 가장 우수합니다.