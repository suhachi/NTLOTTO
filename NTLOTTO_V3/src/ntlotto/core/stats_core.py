import pandas as pd
import numpy as np

def _get_nums(row):
    return [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]

def calc_sum6(df: pd.DataFrame):
    sums = df.apply(lambda row: sum(_get_nums(row)), axis=1)
    mean_val = sums.mean()
    std_val = sums.std()
    
    low_bound = mean_val - 1.2 * std_val
    high_bound = mean_val + 1.2 * std_val
    
    in_range = sums[(sums >= low_bound) & (sums <= high_bound)]
    coverage = len(in_range) / len(sums) * 100 if len(sums) > 0 else 0
    
    return {
        "min": sums.min(),
        "max": sums.max(),
        "mean": mean_val,
        "std": std_val,
        "mu_sub_1_2": low_bound,
        "mu_add_1_2": high_bound,
        "coverage_pct": coverage
    }

def calc_odd_even(df: pd.DataFrame):
    ratios = { "3:3":0, "4:2":0, "2:4":0, "5:1":0, "1:5":0, "6:0":0, "0:6":0 }
    total = len(df)
    
    for _, row in df.iterrows():
        nums = _get_nums(row)
        odd_c = sum(1 for n in nums if n % 2 != 0)
        even_c = 6 - odd_c
        key = f"{odd_c}:{even_c}"
        if key in ratios:
            ratios[key] += 1
            
    pct_ratios = {k: (v/total)*100 for k,v in ratios.items()} if total > 0 else ratios
    extreme = pct_ratios.get("5:1", 0) + pct_ratios.get("1:5", 0) + pct_ratios.get("6:0", 0) + pct_ratios.get("0:6", 0)
    
    return {
        "raw_counts": ratios,
        "pct_map": pct_ratios,
        "extreme_pct": extreme
    }

def calc_bands(df: pd.DataFrame):
    # bands: 1-9, 10-19, 20-29, 30-39, 40-45
    bands = {"1-9": 0, "10-19": 0, "20-29": 0, "30-39": 0, "40-45": 0}
    
    for _, row in df.iterrows():
        nums = _get_nums(row)
        for n in nums:
            if 1 <= n <= 9: bands["1-9"] += 1
            elif 10 <= n <= 19: bands["10-19"] += 1
            elif 20 <= n <= 29: bands["20-29"] += 1
            elif 30 <= n <= 39: bands["30-39"] += 1
            elif 40 <= n <= 45: bands["40-45"] += 1
            
    total_rounds = len(df)
    return {k: v / total_rounds for k, v in bands.items()} if total_rounds > 0 else bands

def calc_runs(df: pd.DataFrame):
    run_dist = {1: 0, 2: 0, 3: 0} # 3 means 3+
    total = len(df)
    
    for _, row in df.iterrows():
        nums = sorted(_get_nums(row))
        max_r = 1
        curr_r = 1
        for i in range(1, len(nums)):
            if nums[i] == nums[i-1] + 1:
                curr_r += 1
                max_r = max(max_r, curr_r)
            else:
                curr_r = 1
                
        if max_r >= 3:
            run_dist[3] += 1
        else:
            run_dist[max_r] += 1
            
    return {k: (v/total)*100 for k,v in run_dist.items()} if total > 0 else run_dist

def calc_same_ends(df: pd.DataFrame):
    dist = {0: 0, 1: 0, 2: 0, 3: 0} # 3 means 3+
    total = len(df)
    
    for _, row in df.iterrows():
        nums = _get_nums(row)
        ends = [n % 10 for n in nums]
        from collections import Counter
        counts = Counter(ends)
        
        # How many groups have 2 or more?
        groups = sum(1 for v in counts.values() if v >= 2)
        
        if groups >= 3:
            dist[3] += 1
        else:
            dist[groups] += 1
            
    return {k: (v/total)*100 for k,v in dist.items()} if total > 0 else dist

def calc_hot_cold(df: pd.DataFrame):
    from collections import Counter
    all_num = []
    for _, row in df.iterrows():
        all_num.extend(_get_nums(row))
        
    c = Counter(all_num)
    # Ensure all 1-45 are present
    for i in range(1, 46):
        if i not in c:
            c[i] = 0
            
    most = c.most_common()
    top10 = most[:10]
    bottom10 = most[-10:] # Least common naturally if sort is correct (most_common returns descending)
    bottom10.reverse() # lowest first
    
    return {
        "top10": top10,
        "bottom10": bottom10,
        "counter": c
    }

def calc_recency_overlaps(df: pd.DataFrame, master_df: pd.DataFrame):
    # Calculates ov_prev1, ov_prev5, ov_prev10 for the given df snapshot.
    # It requires master_df to look backwards.
    ov_1 = []
    ov_5 = []
    ov_10 = []
    
    for _, row in df.iterrows():
        r = row['round']
        current_set = set(_get_nums(row))
        
        # Prev 1
        prev1_df = master_df[master_df['round'] == r - 1]
        if not prev1_df.empty:
            prev1_set = set(_get_nums(prev1_df.iloc[0]))
            ov_1.append(len(current_set.intersection(prev1_set)))
            
        # Prev 5
        prev5_df = master_df[(master_df['round'] >= r - 5) & (master_df['round'] < r)]
        if len(prev5_df) > 0:
            prev5_pool = set()
            for _, p_row in prev5_df.iterrows():
                prev5_pool.update(_get_nums(p_row))
            ov_5.append(len(current_set.intersection(prev5_pool)))
            
        # Prev 10
        prev10_df = master_df[(master_df['round'] >= r - 10) & (master_df['round'] < r)]
        if len(prev10_df) > 0:
            prev10_pool = set()
            for _, p_row in prev10_df.iterrows():
                prev10_pool.update(_get_nums(p_row))
            ov_10.append(len(current_set.intersection(prev10_pool)))
            
    return {
        "ov1_mean": np.mean(ov_1) if ov_1 else 0,
        "ov5_mean": np.mean(ov_5) if ov_5 else 0,
        "ov10_mean": np.mean(ov_10) if ov_10 else 0
    }
