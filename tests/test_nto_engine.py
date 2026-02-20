import pytest
import pandas as pd
import numpy as np
from nt_lotto.nt_engines import nto

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

def test_nto_structure(mock_ssot_df):
    target_round = 31
    
    # It might fail or return empty if actual engines throw errors, but it gracefully falls back.
    # NTO uses live modules. 
    # To test actual aggregation without crashing, it should handle missing engines correctly.
    res = nto.analyze(mock_ssot_df, target_round, k_eval=20)
    
    assert res['engine'] == "NTO"
    assert res['round'] == target_round
    # Depending on imports, topk can be 20. But if no engines are mockable or return list, it might be 20 zeros.
    # Usually it falls back gracefully.
    assert len(res['topk']) == 20
    assert len(res['scores']) == 45
