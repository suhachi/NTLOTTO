# NTLOTTO

**NT Project Lotto Analysis & Prediction Engine**

## Overview
NTLOTTO is a sophisticated lottery prediction framework based on the SSOT (Single Source of Truth) principle. It combines multiple analytical engines (NT4, NT5, NT-LL, VPA, NTO, etc.) to predict lottery outcomes through frequency analysis, deviation correction, and meta-optimization.

## Key Features
- **14 Specialized Engines**: Including frequency-based (NT4), hot-cluster (NT5), local deviation (NT-LL), pattern analysis (VPA), meta-optimization (NTO), and advanced algorithms.
- **Deterministic & Reproducible**: Same input → Same output, every time.
- **SSOT-Driven**: All data sourced from standardized SSOT files (ssot_sorted.csv, ssot_ordered.csv).
- **Golden Tests**: Automated verification of determinism and data exclusion compliance.
- **Operational Pipeline**: Single entry point (`run_round_pipeline.py`) for analysis and prediction.

## Project Structure
```
nt_lotto/
├── nt_core/          # Core utilities (SSOT loader, constants, features)
├── nt_engines/       # 14 prediction engines (NT4, NT5, NT-LL, VPA, etc.)
├── scripts/          # Operational scripts (pipeline, engine runner)
└── ...

data/
├── ssot_sorted.csv   # SSOT: Label/Verdict (Sorted)
├── ssot_ordered.csv  # SSOT: Features (Ordered; AL-only)
└── exclude_rounds.csv # Rounds to exclude from learning/analysis

tests/
├── test_golden_contract.py    # Golden tests (determinism, exclusion)
├── test_nt4_engine.py         # NT4 unit tests
├── test_nt5_engine.py         # NT5 unit tests
└── ...
```

## Quick Start
```bash
# Run pipeline for analysis & prediction
python -m nt_lotto.scripts.run_round_pipeline --round 1211 --mode next

# Run tests
python -m pytest tests/
```

## Status
**Scaffolding/Baseline**: Core architecture and data contracts established. Engines NT4 and NT5 fully implemented. NT-LL, VPA, NT-VPA-1, NTO, NT-Ω in progress.

## Documentation
- [Architecture Report](03_Global_Analysis_Archive/Architecture_Reports/NT_System_Architecture_v2.0_Final.md)
- [Work Completion Report](03_Global_Analysis_Archive/NT_WORK_COMPLETION_REPORT.md)
- [Project Manual](PROJECT_MANUAL_v2.md)

## Author
NT System Architect (Copilot)

## License
Proprietary
