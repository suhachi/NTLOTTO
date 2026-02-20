
import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add project root to path
# tests/ is at root/tests, so we need to add root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nt_lotto.nt_engines import nt_ll
# from nt_lotto.data_loader import SSOTLoader # Incorrect path
# We only need pandas dataframe for this test, so we can mock the loader or just usage.
# The test fixture 'mock_ssot_df' replaces the loader.

@pytest.fixture
def mock_ssot_df():
    # Create valid mock data structure
    # columns: round, date, n1..n6, bonus
    data = []
    for r in range(1, 200):
        # Deterministic generation
        row = {'round': r, 'date': '2000-01-01'}
        for i in range(1, 7):
            row[f'n{i}'] = ((r + i) % 45) + 1
        row['bonus'] = ((r + 7) % 45) + 1
        data.append(row)
    return pd.DataFrame(data)

def test_nt_ll_output_structure(mock_ssot_df):
    """
    Test basic output structure
    """
    target_round = 150
    result = nt_ll.analyze(mock_ssot_df, target_round, k_eval=20)
    
    assert result['engine'] == "NT-LL"
    assert result['round'] == target_round
    assert len(result['topk']) == 20
    assert len(result['scores']) == 45
    
    # Check topk distinct and range
    assert len(set(result['topk'])) == 20
    assert all(1 <= n <= 45 for n in result['topk'])
    
    # Check sorting: Score Desc, then N Asc
    scores = result['scores']
    for i in range(len(scores) - 1):
        s1 = scores[i]
        s2 = scores[i+1]
        
        # Primary: Score Desc
        assert s1['score'] >= s2['score']
        
        # Tie-break: N Asc (only if scores are EFFECTIVELY equal)
        if abs(s1['score'] - s2['score']) < 1e-15:
            assert s1['n'] < s2['n']

def test_nt_ll_determinism(mock_ssot_df):
    """
    Test determinism: Equal inputs -> Equal outputs
    """
    target_round = 150
    res1 = nt_ll.analyze(mock_ssot_df, target_round, k_eval=20)
    res2 = nt_ll.analyze(mock_ssot_df, target_round, k_eval=20)
    
    # TopK should be identical list
    assert res1['topk'] == res2['topk']
    
    # Scores should be effectively identical
    for s1, s2 in zip(res1['scores'], res2['scores']):
        assert s1['n'] == s2['n']
        assert abs(s1['score'] - s2['score']) < 1e-12

def test_nt_ll_no_lookahead(mock_ssot_df):
    """
    Test no-lookahead: Future data should not affect result
    """
    target_round = 100
    
    # Create df with future data
    future_rows = []
    msg_num = 45 # Extreme frequency to bias if leaked
    for r in range(target_round, target_round + 50):
        row = {'round': r, 'date': '2099-01-01'}
        for i in range(1, 7): row[f'n{i}'] = msg_num
        row['bonus'] = msg_num
        future_rows.append(row)
        
    df_future = pd.concat([mock_ssot_df, pd.DataFrame(future_rows)], ignore_index=True)
    
    # Analyze original vs future-contaminated
    # Both targeting 'target_round' (so data >= target_round should be ignored)
    res_clean = nt_ll.analyze(mock_ssot_df, target_round, k_eval=20)
    res_dirty = nt_ll.analyze(df_future, target_round, k_eval=20)
    
    assert res_clean['topk'] == res_dirty['topk']
    
    # Verify exact scores identical
    clean_map = {item['n']: item['score'] for item in res_clean['scores']}
    dirty_map = {item['n']: item['score'] for item in res_dirty['scores']}
    
    for n in range(1, 46):
        assert abs(clean_map[n] - dirty_map[n]) < 1e-12
