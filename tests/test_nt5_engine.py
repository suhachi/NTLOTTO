import pytest
import pandas as pd
from nt_lotto.nt_engines.nt5 import analyze

def test_nt5_output_structure():
    # Mock Data
    data = {
        'round': range(1, 150),
        'n1': [1]*149, 'n2': [2]*149, 'n3': [3]*149, 
        'n4': [4]*149, 'n5': [5]*149, 'n6': [6]*149, 
        'bonus': [7]*149
    }
    df = pd.DataFrame(data)
    
    target_round = 150
    result = analyze(df, target_round)
    
    assert isinstance(result, list)
    assert len(result) == 20
    assert len(set(result)) == 20  # Unique
    assert all(1 <= n <= 45 for n in result)

def test_nt5_determinism():
    # Mock Data
    data = {
        'round': range(1, 100),
        'n1': [10]*99, 'n2': [12]*99, 'n3': [13]*99, 
        'n4': [20]*99, 'n5': [21]*99, 'n6': [22]*99, 
        'bonus': [30]*99
    }
    df = pd.DataFrame(data)
    
    res1 = analyze(df, 100)
    res2 = analyze(df, 100)
    
    assert res1 == res2

def test_nt5_no_lookahead():
    # Setup data where a number only appears in the future (>= target_round)
    data = {
        'round': [1, 2, 3, 4, 5],
        'n1': [1, 2, 3, 4, 5],
        'n2': [11, 12, 13, 14, 15],
        'n3': [21, 22, 23, 24, 25],
        'n4': [31, 32, 33, 34, 35],
        'n5': [41, 42, 43, 44, 45],
        'n6': [6, 7, 8, 9, 10],
        'bonus': [10, 10, 10, 10, 10]
    }
    df = pd.DataFrame(data)
    
    # Target is 3. Only rounds 1, 2 should be used.
    # Future round 5 has '45' (n5). R1, R2 do not have 45.
    # R1 has n1=1, n2=11... n5=41.
    # R2 has n5=42.
    # So 45 should have freq 0 and score 0 (lowest).
    # Since we pick top 20, let's just assert 45 is not in top 5 or just have score 0.
    
    # Better yet, inject a "Super Hot" number in future.
    # R5 has [1,1,1,1,1,1] (impossible in real lotto but works for dataframe)
    # If lookahead existed, 1 would be super hot.
    
    # Let's check 45. In R5 it exists. In R1-R2 it does not.
    # Analyze target=3.
    res = analyze(df, 3)
    
    # Since we have only 2 rounds of history, almost all numbers have low freq.
    # 45 should be at the bottom (score 0, number 45).
    # Top 20 will be numbers present in R1, R2 (about 12 numbers).
    # Then checking tie-breakers (number asc). 1, 2, 3...
    
    # 45 is large index, so it loses tie-break against 1..44 if both score 0.
    # So 45 should NOT be in result if there are enough candidates with score 0 < 45?
    # Wait, 1..45.
    # Candidates with freq > 0: R1(6 nums) + R2(6 nums) = 12 nums.
    # Remaining 33 nums have score 0.
    # Sort Score Desc, Number Asc.
    # Top 12 are non-zero score.
    # Next 8 are zero score, smallest number indices.
    # So 1, 2, 3... that are not in Top 12.
    # 45 is large, it should be near end.
    # Result size 20.
    
    assert 45 not in res
