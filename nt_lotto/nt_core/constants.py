import os

# Base paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Data Directories
DATA_DIR = os.path.join(ROOT_DIR, "data")
ARCHIVE_DIR = os.path.join(ROOT_DIR, "03_Global_Analysis_Archive")
EVAL_DIR = os.path.join(ARCHIVE_DIR, "Evaluations")

# SSOT Files
SSOT_SORTED = os.path.join(DATA_DIR, "ssot_sorted.csv")
SSOT_ORDERED = os.path.join(DATA_DIR, "ssot_ordered.csv")
EXCLUDE_CSV = os.path.join(DATA_DIR, "exclude_rounds.csv")
CONFLICT_CSV = os.path.join(DATA_DIR, "ssot_conflicts.csv")

# Aliases for compatibility
SORTED_CSV = SSOT_SORTED
ORDERED_CSV = SSOT_ORDERED

ENGINES_FIXED = [
    "NT5", "NT4", "NTO", "VPA", "NT-VPA-1", "NT-LL", 
    "NT-PAT", "NT-HCE", "NT-DPP", "NT-EXP",
    "AL1", "AL2", "ALX", "NT-OMEGA"
]

K_EVAL = 20
K_POOL = 22
K_DIAG = [15, 25]

PORTFOLIO_QUOTA_DEFAULT = {
    "NT4": 14,
    "NT-Ω": 14,
    "NT5": 5,
    "VPA": 3,
    "NT-VPA-1": 3,
    "ALX": 5,
    "AL1": 3,
    "AL2": 3
}

QA_DEFAULTS = {
    "max_overlap": 2,
    "max_freq": 8,
    "max_jaccard": 0.30
}

STATE_MODE_DEFAULT = "band_parity"
WINDOWS_DEFAULT = [3, 5, 10, 20, 50]
PAIR_WINDOW_DEFAULT = 300
EW_ALPHA_DEFAULT = 0.93
