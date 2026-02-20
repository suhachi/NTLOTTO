import pytest
import pandas as pd
from nt_lotto.nt_engines.nt_ll import analyze

def test_ntll_output_structure():
    # Mock Data
    data = {
        'round': range(1, 51),
        'n1': [1]*50, 'n2': [2]*50, 'n3': [3]*50, 
        'n4': [4]*50, 'n5': [5]*50, 'n6': [6]*50, 
        'bonus': [7]*50
    }
    df = pd.DataFrame(data)
    
    target_round = 51
    result = analyze(df, target_round)
    
    assert isinstance(result, list)
    assert len(result) == 20
    assert len(set(result)) == 20  # Unique
    assert all(1 <= n <= 45 for n in result)

def test_ntll_determinism():
    # Mock Data
    data = {
        'round': range(1, 30),
        'n1': [10]*29, 'n2': [12]*29, 'n3': [13]*29, 
        'n4': [20]*29, 'n5': [21]*29, 'n6': [22]*29, 
        'bonus': [30]*29
    }
    df = pd.DataFrame(data)
    
    res1 = analyze(df, 30)
    res2 = analyze(df, 30)
    
    assert res1 == res2

def test_ntll_no_lookahead():
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
    res = analyze(df, 3)
    assert 45 not in res
