import pandas as pd
import os
from .constants import SORTED_CSV, ORDERED_CSV, EXCLUDE_CSV

def load_data(exclusion_mode=True):
    """
    Load SSOT data (Sorted & Ordered) and apply exclusions.
    
    Args:
        exclusion_mode (bool): If True, removes rounds listed in exclude_rounds.csv
        
    Returns:
        tuple: (df_sorted, df_ordered)
    """
    # Load SSOT
    if not os.path.exists(SORTED_CSV):
        raise FileNotFoundError(f"SSOT Sorted not found: {SORTED_CSV}")
    if not os.path.exists(ORDERED_CSV):
        raise FileNotFoundError(f"SSOT Ordered not found: {ORDERED_CSV}")
        
    df_sorted = pd.read_csv(SORTED_CSV)
    df_ordered = pd.read_csv(ORDERED_CSV)
    
    # Load Exclusions
    exclude_list = []
    if exclusion_mode and os.path.exists(EXCLUDE_CSV):
        # PATCH: Handle comments starting with '#'
        df_exclude = pd.read_csv(EXCLUDE_CSV, comment='#')
        if 'round' in df_exclude.columns:
            exclude_list = df_exclude['round'].tolist()
            
    # Apply Exclusions
    if exclude_list:
        df_sorted = df_sorted[~df_sorted['round'].isin(exclude_list)]
        df_ordered = df_ordered[~df_ordered['round'].isin(exclude_list)]
        
    return df_sorted, df_ordered

def get_round_data(round_num, df_sorted):
    """Get specific round data."""
    return df_sorted[df_sorted['round'] == round_num]
