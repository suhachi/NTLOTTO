from __future__ import annotations
from pathlib import Path

def assert_ssot_files(sorted_path: str, ordered_path: str) -> None:
    if not Path(sorted_path).exists():
        raise FileNotFoundError(f"[CONTRACT_FAIL] ssot_sorted not found: {sorted_path}")
    if not Path(ordered_path).exists():
        raise FileNotFoundError(f"[CONTRACT_FAIL] ssot_ordered not found: {ordered_path}")
