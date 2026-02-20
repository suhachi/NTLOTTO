import pytest
import pandas as pd
import numpy as np
from nt_lotto.nt_engines import vpa

@pytest.fixture
def mock_ssot_df():
    # 간단한 30회차 이력 데이터 (round 1~30)
    data = []
    np.random.seed(42)
    for r in range(1, 31):
        # 1~45 중 7개 뽑기 (당첨6 + 보너스1)
        nums = np.random.choice(range(1, 46), size=7, replace=False)
        nums.sort()  # 보통 정렬되어있지만, 보너스는 마지막
        row = {'round': r}
        for i in range(1, 7):
            row[f'num{i}'] = nums[i-1]
        row['bonus'] = nums[6]
        data.append(row)
        
    return pd.DataFrame(data)

def test_vpa_determinism(mock_ssot_df):
    target_round = 31
    res1 = vpa.analyze(mock_ssot_df, target_round)
    res2 = vpa.analyze(mock_ssot_df, target_round)
    
    assert len(res1['topk']) == 20
    assert len(res2['topk']) == 20
    assert res1['topk'] == res2['topk']
    
def test_vpa_structure(mock_ssot_df):
    target_round = 31
    res = vpa.analyze(mock_ssot_df, target_round, k_eval=20)
    
    assert res['engine'] == "VPA"
    assert res['round'] == target_round
    assert len(res['scores']) == 45
    assert len(res['topk']) == 20
    
    # Check bounds
    for info in res['scores']:
        assert 1 <= info['n'] <= 45
        assert 0.0 <= info['score'] <= 1.0

def test_vpa_lookahead(mock_ssot_df):
    target_round = 20
    
    # R이 20일 때, 20 이상의 데이터가 들어가면 안 됨.
    # mock_ssot_df는 30까지 존재.
    res = vpa.analyze(mock_ssot_df, target_round)
    
    # 20회차까지만 존재하는 df를 넘겼을 때와 결과가 같아야 함
    past_only_df = mock_ssot_df[mock_ssot_df['round'] < target_round]
    res_past_only = vpa.analyze(past_only_df, target_round)
    
    assert res['topk'] == res_past_only['topk']
