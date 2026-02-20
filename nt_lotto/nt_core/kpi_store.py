# nt_lotto/nt_core/kpi_store.py
import pandas as pd
import os
from typing import List
from .constants import K_EVAL

def update_engine_recall_summary(csv_path: str, round_num: int, engine_name: str, k: int, recalls: dict):
    """
    Append or update recall summary for an engine.
    recalls: {"mean_all": ..., "mean_last10": ..., "mean_last20": ..., "mean_last30": ...}
    """
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=["round", "engine", "k", "mean_all", "mean_last10", "mean_last20", "mean_last30"])
    
    # Remove existing record if same round/engine/k
    df = df[~((df["round"] == round_num) & (df["engine"] == engine_name) & (df["k"] == k))]
    
    new_row = {
        "round": round_num,
        "engine": engine_name,
        "k": k,
        **recalls
    }
    
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.sort_values(["round", "engine"], inplace=True)
    df.to_csv(csv_path, index=False)

def build_recall_md_report(csv_path: str, md_path: str):
    if not os.path.exists(csv_path): return
    df = pd.read_csv(csv_path)
    # Get latest round per engine
    latest_df = df.sort_values("round").groupby("engine").last().reset_index()
    
    md_text = "# Engine Recall Summary (KPI Table)\n\n"
    md_text += f"**K_EVAL**: {K_EVAL}\n\n"
    md_text += latest_df.to_markdown(index=False)
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
