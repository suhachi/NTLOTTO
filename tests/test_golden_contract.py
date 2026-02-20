import pytest
import subprocess
import sys
import os
import hashlib
import pandas as pd
from nt_lotto.nt_core.constants import EXCLUDE_CSV

# Utility to compute file hash
def compute_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

@pytest.mark.golden
def test_pipeline_determinism(tmp_path):
    """
    Golden Test: Determinism (Task A)
    Running the pipeline twice with the same inputs must produce identical outputs.
    """
    # Use a recent round for testing (e.g., 1210 to predict 1211)
    test_round = "1210"
    mode = "next"
    
    # Define output files to verify
    # Note: We are running in the actual workspace to ensure environment consistency, 
    # but strictly checking the file consistency.
    # In a real CI, we might use tmp_path for out_root, but here we run against the project structure
    # to match the user's manual verification method.
    # To avoid polluting main archive, we can use a temp output root.
    
    out_root = str(tmp_path / "test_archive")
    
    cmd = [
        sys.executable, "-m", "nt_lotto.scripts.run_round_pipeline",
        "--round", test_round,
        "--mode", mode,
        "--out_root", out_root
    ]
    
    # Run 1
    subprocess.check_call(cmd)
    pool_file = os.path.join(out_root, "Omega_Pools", str(int(test_round)+1), "omega_pool_K22.csv")
    assert os.path.exists(pool_file), "Omega Pool file not created in Run 1"
    hash1 = compute_file_hash(pool_file)
    
    # Run 2
    subprocess.check_call(cmd)
    assert os.path.exists(pool_file), "Omega Pool file not created in Run 2"
    hash2 = compute_file_hash(pool_file)
    
    assert hash1 == hash2, "Pipeline is NON-DETERMINISTIC! Hashes do not match."

@pytest.mark.golden
def test_exclude_rounds_compliance():
    """
    Golden Test: Exclude Rounds (Task A)
    Verify that excluded rounds are not present in the SSOT loaded by the loader.
    """
    from nt_lotto.nt_core.ssot_loader import load_data
    
    # Ensure exclude file exists or mock it
    if not os.path.exists(EXCLUDE_CSV):
        pytest.skip("exclude_rounds.csv not found")
        
    # Read raw exclusions
    df_exclude = pd.read_csv(EXCLUDE_CSV, comment='#')
    if 'round' not in df_exclude.columns:
        pytest.skip("Invalid exclude_rounds.csv format")
        
    excluded_rounds = df_exclude['round'].tolist()
    
    # Load via Loader
    df_sorted, df_ordered = load_data(exclusion_mode=True)
    
    # Check intersection
    sorted_rounds = df_sorted['round'].unique()
    intersection = set(sorted_rounds).intersection(set(excluded_rounds))
    
    assert len(intersection) == 0, f"Excluded rounds found in Loaded SSOT: {intersection}"
