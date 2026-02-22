#!/usr/bin/env bash

echo "[NTLOTTO v3] Starting Sprint A Pipeline..."

# 1. Virtual Environment Check
if [ -z "$VIRTUAL_ENV" ]; then
    echo "[Warning] Python virtual environment (venv) is NOT active."
    echo "Recommendation: Create and activate a venv first:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate  # (Windows: venv\Scripts\activate)"
    echo "--------------------------------------------------------"
fi

# 2. Install Requirements
echo ">> Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# 3. Run Pipeline (Validate + Generate WHY Reports)
echo ">> Running Data Validation and Generating Reports (Target Round: 1213)..."
python -m ntlotto.cli.make_why_reports --round 1213 --long 100 --short 5,10,15,20,25,30

# 4. List Check
echo ">> Pipeline Finished. Checking output directories..."
echo "[docs/reports/latest/]"
ls -l docs/reports/latest/

echo ""
echo "[docs/reports/history/] (Last 5)"
ls -l docs/reports/history/ | tail -n 5

echo "[SUCCESS] Sprint A Execution Completed."
