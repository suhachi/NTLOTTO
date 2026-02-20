# Allocation Decision Sheet
**Purpose:** Provide data-driven evaluation to allocate resources combinations/budget.
## Grading Criteria
- **A Class (Increase):** `recall_mean` is in top 2 AND `stability` >= 0.70 AND `drift` >= -0.10
- **C Class (Decrease):** `recall_mean` is in bottom 2 OR `stability` < 0.60 OR `drift` <= -0.25
- **B Class (Maintain):** All other engines.

## Engine Performance Overview
| Engine | Grade | Recall Mean | Std | Stability | Drift(Rec-Past) | Bonus Hit |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| NT-Omega | **B** | 3.08 | 1.08 | 0.68 | +0.09 | 0.45 |
| NT-LL | **C** | 2.92 | 1.18 | 0.85 | -0.46 | 0.40 |
| NT-VPA-1 | **B** | 2.81 | 1.07 | 0.62 | +0.11 | 0.35 |
| NTO | **B** | 2.80 | 1.11 | 0.65 | +0.00 | 0.41 |
| NT5 | **B** | 2.77 | 1.14 | 0.79 | -0.21 | 0.44 |
| NT4 | **C** | 2.75 | 1.19 | 0.89 | -0.25 | 0.46 |
| VPA | **C** | 2.72 | 1.12 | 0.59 | +0.41 | 0.36 |