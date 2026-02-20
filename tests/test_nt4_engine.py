import pytest
import pandas as pd
from nt_lotto.nt_engines.nt4 import analyze

def test_nt4_output_structure():
    # Mock Data
    data = {
        'round': range(1, 101),
        'n1': [1]*100, 'n2': [2]*100, 'n3': [3]*100, 
        'n4': [4]*100, 'n5': [5]*100, 'n6': [6]*100, 
        'bonus': [7]*100
    }
    df = pd.DataFrame(data)
    
    target_round = 101
    result = analyze(df, target_round)
    
    assert isinstance(result, list)
    assert len(result) == 20
    assert len(set(result)) == 20  # Unique
    assert all(1 <= n <= 45 for n in result)

def test_nt4_determinism():
    # Mock Data
    data = {
        'round': range(1, 50),
        'n1': [1]*49, 'n2': [2]*49, 'n3': [3]*49, 
        'n4': [10]*49, 'n5': [11]*49, 'n6': [12]*49, 
        'bonus': [20]*49
    }
    df = pd.DataFrame(data)
    
    res1 = analyze(df, 50)
    res2 = analyze(df, 50)
    
    assert res1 == res2

def test_nt4_lookahead_prevention():
    # Ensure it doesn't use data from target_round or future
    data = {
        'round': [1, 2, 3],
        'n1': [1, 1, 1], 'n2': [2, 2, 2], 'n3': [3, 3, 3],
        'n4': [4, 4, 4], 'n5': [5, 5, 5], 'n6': [6, 6, 6],
        'bonus': [7, 7, 7]
    }
    df = pd.DataFrame(data)
    
    # If target is 2, it should only see round 1.
    # Round 1 has [1,2,3,4,5,6] twice (no, wait, logic filters < target)
    
    # Let's verify behavior manually by injecting a distinct number in the future
    # Round 3 has '45'
    data_future = data.copy()
    data_future['n1'] = [1, 1, 45] # Round 3 has 45
    df_future = pd.DataFrame(data_future)
    
    # Target 3 (Should NOT see Round 3)
    res = analyze(df_future, 3)
    
    # If it saw 45, 45 might be in top 20 if logic favored it (freq=1 vs 0).
    # But here 45 is only in R3.
    # Correct logic uses history < 3 (R1, R2). 45 is not in R1, R2.
    # So 45 should have freq 0.
    
    # Wait, result is top 20. If 45 is 0 freq, it will be at bottom unless random.
    # Our logic sorts score desc, number asc.
    # Freq 0 numbers: score 0. Sorted by number asc. 
    # 45 is max number. It should be last.
    
    assert 45 not in res
