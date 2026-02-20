import pandas as pd
import numpy as np

def extract_slot_bias(df_ordered, window=50):
    """
    Analyze number distribution per slot (position 1~6) over recent window.
    """
    recent_df = df_ordered.tail(window)
    slot_stats = {}
    
    for i in range(1, 7):
        col_name = f'n{i}'  # Assuming columns are n1..n6 or similar in ordered CSV
        if col_name in recent_df.columns:
             slot_stats[i] = recent_df[col_name].value_counts().sort_index()
        else:
            # Fallback if column names differ, simply take i-th column (index 0 is round)
            slot_stats[i] = recent_df.iloc[:, i].value_counts().sort_index()
            
    return slot_stats
