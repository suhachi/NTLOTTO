# Exclude Application Verification

- Configured Excludes: 0 rounds (Active)
- Note: The file `exclude_rounds.csv` contains example rows starting with `#`.
- **Parsing Patch Applied**: `ssot_loader.py` was updated to ignore lines starting with `#` using `pd.read_csv(..., comment='#')`. Prior to patch, it attempts to load `#` as a round.

## Verification on SSOT Sorted
- Total Rows in SSOT: 606
- Excluded Rounds STILL PRESENT: 0
  - [PASS] No excluded rounds found in SSOT data.

