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
    
    # Structure to hold results
    engine_results = []
    
    for engine_name in ENGINES:
        logger.info(f"Executing {engine_name}...")
        
        # 1. Execute Engine Logic
        prediction = []
        try:
            if engine_name == "NT4":
                from nt_lotto.nt_engines.nt4 import analyze as analyze_nt4
                # Need to load SSOT here or pass it?
                # The prompt implies run_engines might handle data loading or engines load it.
                # Since SSOT is distinct, let's load it once at the top of main if possible,
                # but to avoid overhead for stubs, we might load it inside.
                # However, for efficiency, load once.
                
                # Check if 'ssot_sorted' is available. 
                # We need to import loader.
                from nt_lotto.nt_core.ssot_loader import load_data
                if 'df_sorted_cache' not in globals():
                    global df_sorted_cache
                    df_sorted_cache, _ = load_data(exclusion_mode=True)
                
                prediction = analyze_nt4(df_sorted_cache, target_round)
            elif engine_name == "NT5":
                from nt_lotto.nt_engines.nt5 import analyze as analyze_nt5
                from nt_lotto.nt_core.ssot_loader import load_data
                if 'df_sorted_cache' not in globals():
                    global df_sorted_cache
                    df_sorted_cache, _ = load_data(exclusion_mode=True)
                
                prediction = analyze_nt5(df_sorted_cache, target_round)
            elif engine_name == "NT-LL":
                from nt_lotto.nt_engines.nt_ll import analyze as analyze_ntll
                from nt_lotto.nt_core.ssot_loader import load_data
                if 'df_sorted_cache' not in globals():
                    global df_sorted_cache
                    df_sorted_cache, _ = load_data(exclusion_mode=True)
                prediction = analyze_ntll(df_sorted_cache, target_round)
            else:
                prediction = get_engine_stub_prediction(engine_name, target_round)
        except Exception as e:
            logger.error(f"Error executing {engine_name}: {e}")
            prediction = []

        # 2. Validation (Length check)
        if len(prediction) > 0:
            # Check K
            pass
            
        # 3. Store Result
        # Format for engine_topk_K20.csv: engine_id, numbers (list)
        engine_results.append({
            "engine_id": engine_name,
            "numbers": prediction
        })
        
    # Save to CSV
    out_csv = os.path.join(out_dir, "engine_topk_K20.csv")
    df = pd.DataFrame(engine_results)
    df.to_csv(out_csv, index=False)
    logger.info(f"Saved engine results to {out_csv}")

if __name__ == "__main__":
    main()
