# NTO Weights Update (N=100)
Generated At: 202602d_0034

## Update Meta
- **ETA**: 0.1 / **CLIP**: 0.05
- **Stability Floor**: 0.6 / **Delta Threshold**: 0.15

## Weights Transition
| Engine | Prev | New | Status |
| :--- | :---: | :---: | :---: |
| NT4 | 0.2000 | 0.2000 | NO_ADV |
| NT5 | 0.2000 | 0.2000 | NO_ADV |
| NT-LL | 0.2000 | 0.2000 | NO_ADV |
| VPA | 0.2000 | 0.2000 | NO_ADV |
| NT-VPA-1 | 0.2000 | 0.2000 | NO_ADV |

## Rationale
- NT4 no_advantage: Direction inconsistent or CI overlap.
- NT5 no_advantage: Direction inconsistent or CI overlap.
- NT-LL no_advantage: Direction inconsistent or CI overlap.
- VPA no_advantage: Low stability (0.59 < 0.6).
- NT-VPA-1 no_advantage: Direction inconsistent or CI overlap.
- Global No Advantage. Keeping weights uniform.