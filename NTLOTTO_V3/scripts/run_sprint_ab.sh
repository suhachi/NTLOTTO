#!/usr/bin/env bash
export PYTHONPATH="src"

echo "=========================================="
echo "NTLOTTO v3: Sprint A+B (리포트 생성)"
echo "=========================================="

echo "[1/3] Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

echo "[2/3] Running Validation & Report Generation Pipeline..."
python -m ntlotto.cli.make_reports --r 1211 --w_long 100 --w_short "5,10,15,20,25,30"

echo "[3/3] Generated Files in docs/reports/latest/"
ls -la docs/reports/latest
echo "=========================================="
