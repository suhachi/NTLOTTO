import pandas as pd

def extract_basic_stats(df_sorted):
    """
    Extract basic frequency statistics from sorted data.
    """
    # Flatten all numbers to calculate global frequency
    all_nums = df_sorted.iloc[:, 1:7].values.flatten()
    freq_series = pd.Series(all_nums).value_counts().sort_index()
    
    # Fill missing numbers with 0
    full_freq = pd.Series(0, index=range(1, 46))
    full_freq.update(freq_series)
    
    return full_freq

def extract_recent_stats(df_sorted, window=30):
    """
    Extract frequency from the last 'window' rounds.
    """
    recent_df = df_sorted.tail(window)
    all_nums = recent_df.iloc[:, 1:7].values.flatten()
    freq_series = pd.Series(all_nums).value_counts().sort_index()
    
    full_freq = pd.Series(0, index=range(1, 46))
    full_freq.update(freq_series)
    
    return full_freq
