import pytest
import pandas as pd
import numpy as np
from nt_lotto.nt_engines import nt_omega

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

def test_nt_omega_structure(mock_ssot_df):
    target_round = 31
    res = nt_omega.analyze(mock_ssot_df, target_round, k_eval=20, k_pool=22)
    
    assert res['engine'] == "NT-OMEGA"
    assert res['round'] == target_round
    assert len(res['topk']) == 22, "Omega must return K_pool=22 by default"
    assert len(res['scores']) == 45
