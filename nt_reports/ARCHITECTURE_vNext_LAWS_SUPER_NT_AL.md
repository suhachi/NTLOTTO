# Architecture: NT Project vNext (Laws -> SuperEngine -> NT/AL)

## 📐 Unified Flow Diagram (ASCII)
```
[ SSOT (Immutable) ]
      |
      v
[ Shared Features (Draw7) ]
      |
      +-----------------------------+
      |                             |
      v                             v
[ Law Modules (1..N) ]      [ NT/AL Prediction Engines ]
      | (LawSignal: Score/Unc)      | (Native Score)
      v                             |
[ SuperEngine (Meta) ]              |
      | (SuperSignal: DeltaWeight)  |
      +-----------------------------+
                                    | (Fused Mode)
                                    v
                        [ Final 6-num Predictions ]
                                    |
                                    v
                        [ Post-draw Scoring/Logs ]
```

## 🧩 Protocol Definitions
- **LawModule**: Independent analyzers. Input: `History + Features`. Output: `LawSignal`.
- **SuperEngine**: Meta-aggregator. Input: `LawSignals`. Output: `SuperSignal`.
- **PredictionEngine**: Terminal units. Input: `Native Logic + (Optional) SuperSignal`. Output: `6-combo CSV`.

## 🚀 Pipeline Steps
1.  **Validate**: `python scripts/01_build_ssot_validate.py`
2.  **Features**: `python scripts/02_build_features.py`
3.  **Train**: `python scripts/03_train.py` (Trains Laws -> Super -> Engines)
4.  **Predict**: `python scripts/05_predict.py --target_round 1208`
5.  **Score**: `python scripts/06_postdraw.py --round 1208`

## 📂 Key Artifacts
- **Laws**: `00_data/derived/laws/{id}/law_state_latest.pkl`
- **Super**: `00_data/derived/super/super_state_latest.pkl`
- **Predictions**: `nt_reports/predictions/predictions_{round}.csv`
- **History**: `nt_reports/performance_history.jsonl`
