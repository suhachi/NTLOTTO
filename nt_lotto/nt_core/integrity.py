# nt_lotto/nt_core/integrity.py
import pandas as pd
import os

def validate_draw(ordered_numbers: list[int], bonus: int) -> tuple[bool, list[str]]:
    """
    Check draw integrity: 6 unique numbers, range 1-45, bonus not in numbers.
    """
    reasons = []
    
    if len(ordered_numbers) != 6:
        reasons.append(f"Invalid count: expected 6, got {len(ordered_numbers)}")
    
    if len(set(ordered_numbers)) != 6:
        reasons.append("Duplicate numbers found in main draw")
        
    for n in ordered_numbers:
        if not (1 <= n <= 45):
            reasons.append(f"Number out of range (1-45): {n}")
            
    if not (1 <= bonus <= 45):
        reasons.append(f"Bonus out of range (1-45): {bonus}")
        
    if bonus in ordered_numbers:
        reasons.append(f"Bonus {bonus} is already in the main numbers")
        
    return (len(reasons) == 0, reasons)

def append_ssot_rows(sorted_path: str, ordered_path: str, round_num: int, date_str: str, ordered: list[int], bonus: int) -> None:
    """
    Append new draw data to Sorted and Ordered SSOT CSVs.
    Follows idempotency: skip if exists, error if exists with different values.
    """
    # 1. Prepare data
    sorted_nums = sorted(ordered)
    new_ord_data = [round_num, date_str] + ordered + [bonus]
    new_srt_data = [round_num, date_str] + sorted_nums + [bonus]
    
    # 2. Check and Append
    for path, new_row_data, cols in [
        (ordered_path, new_ord_data, ["round","date","b1","b2","b3","b4","b5","b6","bonus"]),
        (sorted_path, new_srt_data, ["round","date","n1","n2","n3","n4","n5","n6","bonus"])
    ]:
        if not os.path.exists(path):
            pd.DataFrame([new_row_data], columns=cols).to_csv(path, index=False)
            continue
            
        df = pd.read_csv(path)
        if round_num in df["round"].values:
            existing = df[df["round"] == round_num].iloc[0].tolist()
            # Compare (ignore date if empty)
            if existing[2:] != new_row_data[2:]:
                raise ValueError(f"Round {round_num} data conflict in {path}. Modification forbidden.")
            print(f"[INFO] Round {round_num} already exists in {os.path.basename(path)}. Skipping.")
            continue
            
        new_row_df = pd.DataFrame([new_row_data], columns=cols)
        df = pd.concat([df, new_row_df], ignore_index=True).sort_values("round")
        df.to_csv(path, index=False)

def mark_as_excluded(round_num: int, reason: str):
    from .constants import EXCLUDE_CSV
    from datetime import datetime
    os.makedirs(os.path.dirname(EXCLUDE_CSV), exist_ok=True)
    df = pd.read_csv(EXCLUDE_CSV) if os.path.exists(EXCLUDE_CSV) else pd.DataFrame(columns=["round","reason","created_at"])
    if round_num not in df["round"].values:
        new_row = {"round": round_num, "reason": reason, "created_at": datetime.now().isoformat()}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(EXCLUDE_CSV, index=False)
