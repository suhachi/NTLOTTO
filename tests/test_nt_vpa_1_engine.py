import pytest
import pandas as pd
import numpy as np
from nt_lotto.nt_engines import nt_vpa_1

@pytest.fixture
def mock_ssot_df():
    data = []
    np.random.seed(42)
    for r in range(1, 31):
        nums = np.random.choice(range(1, 46), size=7, replace=False)
        row = {'round': r}
        for i in range(1, 7):
            row[f'num{i}'] = nums[i-1]
        row['bonus'] = nums[6]
        data.append(row)
    return pd.DataFrame(data)

def test_nt_vpa_1_determinism_and_structure(mock_ssot_df):
    target_round = 31
    res = nt_vpa_1.analyze(mock_ssot_df, target_round, k_eval=20)
    
    assert res['engine'] == "NT-VPA-1"
    assert len(res['scores']) == 45
    assert len(res['topk']) == 20
    
    # Ensure stability is present
    sample = res['scores'][0]
    assert 'stability' in sample
    assert 'evidence' in sample
