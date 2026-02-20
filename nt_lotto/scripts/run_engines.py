import argparse
import sys
import os
import logging
import pandas as pd
from typing import List, Dict

# Adjust path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from nt_lotto.nt_core.constants import SSOT_SORTED, SSOT_ORDERED, K_EVAL
# We don't import actual engines because they are dynamic or many.
# For scaffolding, we will import the registry or mock them.
# Assuming we have a `nt_lotto/nt_engines/__init__.py` or similar to discover engines.
# Since user says "14 Engines Fixed", we can hardcode the list.

# Engine List
ENGINES = [
    "NT4", "NT-Omega", "NT5", "NTO", "NT-LL", "VPA", "NT-VPA-1", 
    "AL1", "AL2", "ALX", "NT-EXP", "NT-DPP", "NT-HCE", "NT-PAT"
]

# Logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("EngineRunner")

# Global Cache
df_sorted_cache = None

def get_engine_stub_prediction(engine_name: str, target_round: int) -> List[int]:
    """
    Simulates engine prediction.
    In real implementation, this would import the engine module and call `analyze`.
    """
    # Try to import engine module dynamically
    try:
        # Normalization: NT-Omega -> nt_omega ?
        # For now, just return a dummy stub or check if file exists.
        module_name = engine_name.lower().replace("-", "_")
        # spec = importlib.util.find_spec(f"nt_lotto.nt_engines.{module_name}")
        # if spec: ...
        pass
    except Exception:
        pass
        
    # STUB BEHAVIOR: Return empty list or random for scaffolding testing?
    # User instructions: "Implementation Sprint" -> Logic is empty.
    # We should return an empty list or a placeholder that indicates "Not Implemented".
    # BUT, to test the pipeline (Recall calc, Omega), we might want dummy data?
    # No, strict SSOT. If engine is stub, it returns nothing or logs warning.
    
    logger.warning(f"Engine {engine_name} is a STUB. No prediction for {target_round}.")
    return []

def main():
    parser = argparse.ArgumentParser(description="Run all 14 engines for a target round")
    parser.add_argument("--target", type=int, required=True, help="Target Round (R+1)")
    parser.add_argument("--out_dir", type=str, required=True, help="Output directory for Omega Pools/Engine Results")
    
    args = parser.parse_args()
    
    target_round = args.target
    out_dir = args.out_dir
    os.makedirs(out_dir, exist_ok=True)
    
    logger.info(f"Running Engines for Target Round {target_round}...")
    
    # 0. Global Cache & Data Loader
    global df_sorted_cache
    from nt_lotto.nt_core.ssot_loader import load_data
    
    if df_sorted_cache is None:
        df_sorted_cache, _ = load_data(exclusion_mode=True)
        
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%md_%H%M")
    report_data = {
        "target_round": target_round,
        "timestamp": timestamp,
        "engines": {}
    }
    
    # Structure to hold results
    engine_results = []
    
    for engine_name in ENGINES:
        logger.info(f"Executing {engine_name}...")
        
        # 1. Execute Engine Logic
        prediction = []
        diagnostics = {}
        
        try:
            if engine_name == "NT4":
                from nt_lotto.nt_engines.nt4 import analyze
                res = analyze(df_sorted_cache, target_round)
            elif engine_name == "NT5":
                from nt_lotto.nt_engines.nt5 import analyze
                res = analyze(df_sorted_cache, target_round)
            elif engine_name == "NT-LL":
                from nt_lotto.nt_engines.nt_ll import analyze
                res = analyze(df_sorted_cache, target_round)
            elif engine_name == "VPA":
                from nt_lotto.nt_engines.vpa import analyze
                res = analyze(df_sorted_cache, target_round)
            elif engine_name == "NT-VPA-1":
                from nt_lotto.nt_engines.nt_vpa_1 import analyze
                res = analyze(df_sorted_cache, target_round)
            elif engine_name == "NTO":
                from nt_lotto.nt_engines.nto import analyze
                res = analyze(df_sorted_cache, target_round)
            elif engine_name == "NT-Omega":
                from nt_lotto.nt_engines.nt_omega import analyze
                res = analyze(df_sorted_cache, target_round)
            elif engine_name in ["AL1", "AL2", "ALX"]:
                from nt_lotto.nt_engines.al_engines import analyze
                res = analyze(engine_name, df_sorted_cache, target_round)
            elif engine_name in ["NT-EXP", "NT-DPP", "NT-HCE", "NT-PAT"]:
                from nt_lotto.nt_engines.diagnostic_stubs import analyze
                res = analyze(engine_name, df_sorted_cache, target_round)
            else:
                res = get_engine_stub_prediction(engine_name, target_round)
                
            prediction = res['topk'] if isinstance(res, dict) and 'topk' in res else (res if isinstance(res, list) else [])
            diagnostics = res.get('diagnostics', {}) if isinstance(res, dict) else {}
            
            # Extract engine params and evidence for reporting
            report_data["engines"][engine_name] = {
                "topk": prediction,
                "diagnostics": diagnostics,
                "params": res.get("params", {}) if isinstance(res, dict) else {}
            }
            
        except Exception as e:
            logger.error(f"Error executing {engine_name}: {e}")
            prediction = []
            report_data["engines"][engine_name] = {"error": str(e)}

        # 3. Store Result
        engine_results.append({
            "engine_id": engine_name,
            "numbers": prediction
        })
        
    # Save to CSV
    out_csv = os.path.join(out_dir, "engine_topk_K20.csv")
    pd.DataFrame(engine_results).to_csv(out_csv, index=False)
    logger.info(f"Saved engine results to {out_csv}")
    
    # Save JSON Report
    latest_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../docs/reports/latest'))
    history_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../docs/reports/history'))
    os.makedirs(latest_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)
    
    json_name = f"Round_{target_round}_Evaluation.json"
    dict_out = report_data
    
    with open(os.path.join(history_dir, f"{timestamp}_{json_name}"), 'w', encoding='utf-8') as f:
        json.dump(dict_out, f, ensure_ascii=False, indent=2)
    with open(os.path.join(latest_dir, json_name), 'w', encoding='utf-8') as f:
        json.dump(dict_out, f, ensure_ascii=False, indent=2)
        
    # Save MD Report
    md_name = f"Round_{target_round}_Evaluation_Report.md"
    md_lines = [f"# Evaluation Report (Round {target_round})", f"Generated: {timestamp}\n"]
    
    for en, data in report_data["engines"].items():
        md_lines.append(f"## {en}")
        if "error" in data:
            md_lines.append(f"**Error**: {data['error']}\n")
            continue
            
        md_lines.append(f"- **TopK**: {data.get('topk', [])}")
        diag = data.get('diagnostics', {})
        if diag:
            md_lines.append(f"- **Diagnostics**: {diag}")
        md_lines.append("")
        
    md_content = "\n".join(md_lines)
    
    with open(os.path.join(history_dir, f"{timestamp}_{md_name}"), 'w', encoding='utf-8') as f:
        f.write(md_content)
    with open(os.path.join(latest_dir, md_name), 'w', encoding='utf-8') as f:
        f.write(md_content)
        
    logger.info(f"Generated evaluation reports in docs/reports/latest/")

if __name__ == "__main__":
    main()
