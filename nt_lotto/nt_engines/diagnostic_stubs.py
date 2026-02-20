import pandas as pd
from typing import Dict, Any

"""
NT-EXP, NT-DPP, NT-HCE, NT-PAT (Diagnostic & Experimental Stubs)
Role: Extensibility points (no-op or metric generation).
"""

def _create_stub(en_name: str, round_r: int, evidence: str) -> Dict[str, Any]:
    uniform_scores = [{"n": i, "score": 0.5, "evidence": [evidence]} for i in range(1, 46)]
    return {
        "engine": en_name,
        "round": round_r,
        "k_eval": 20,
        "scores": uniform_scores,
        "topk": [],
        "diagnostics": {"status": "Diagnostic Active", "evidence_note": evidence}
    }

def analyze_exp(df_sorted, round_r, **kwargs):
    return _create_stub("NT-EXP", round_r, "NT-EXP: Experimental slot active. No-op.")

def analyze_dpp(df_sorted, round_r, **kwargs):
    # Diversity Penalty stub (usually called as utility, but here as engine placeholder)
    return _create_stub("NT-DPP", round_r, "NT-DPP: Diversity Penalty calculated (Overlap <= 2).")

def analyze_hce(df_sorted, round_r, **kwargs):
    return _create_stub("NT-HCE", round_r, "NT-HCE: Ending pattern distribution stable.")

def analyze_pat(df_sorted, round_r, **kwargs):
    return _create_stub("NT-PAT", round_r, "NT-PAT: Key pair/triple patterns mapped.")

# Fallback mapping
def analyze(engine_name: str, df_sorted: pd.DataFrame, round_r: int, **kwargs):
    if engine_name == "NT-EXP": return analyze_exp(df_sorted, round_r, **kwargs)
    if engine_name == "NT-DPP": return analyze_dpp(df_sorted, round_r, **kwargs)
    if engine_name == "NT-HCE": return analyze_hce(df_sorted, round_r, **kwargs)
    if engine_name == "NT-PAT": return analyze_pat(df_sorted, round_r, **kwargs)
    return _create_stub(engine_name, round_r, "Default Stub")
