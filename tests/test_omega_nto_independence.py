import pytest
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from nt_lotto.nt_core.ssot_loader import load_data

def test_omega_nto_independence():
    """
    Test that NT-Omega and NTO do not produce exactly the same Top20 rankings.
    This guarantees Omega has independent evaluation power.
    """
    from nt_lotto.nt_engines.nto import analyze as nto_analyze
    from nt_lotto.nt_engines.nt_omega import analyze as omega_analyze
    
    df, _ = load_data(exclusion_mode=True)
    
    # Pick a few recent rounds
    max_round = df['round'].max()
    sample_rounds = [max_round - i for i in range(3)]
    
    jaccards = []
    
    for r in sample_rounds:
        # Get NTO top 20
        res_nto = nto_analyze(df, r, k_eval=20)
        topk_nto = set(res_nto.get('topk', [])[:20])
        
        # Get Omega top 20
        res_omega = omega_analyze(df, r, k_eval=20)
        topk_omega = set(res_omega.get('topk', [])[:20])
        
        # intersection over union
        intersect = topk_nto & topk_omega
        union = topk_nto | topk_omega
        j_idx = len(intersect) / len(union) if len(union) > 0 else 1.0
        
        jaccards.append(j_idx)
        
    # At least one round should have Jaccard < 1.0
    # Meaning they are not 100% identical
    assert any(j < 1.0 for j in jaccards), f"NT-Omega is still an exact clone of NTO! Jaccards: {jaccards}"
