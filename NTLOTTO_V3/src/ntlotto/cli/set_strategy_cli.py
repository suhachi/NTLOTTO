from __future__ import annotations
import argparse, json
from pathlib import Path

from ntlotto.contracts.engine_contract import ENGINE_KEYS, assert_engine_keys_map
from ntlotto.contracts.constitution_contract import assert_constitution
from ntlotto.cli._io_formats import parse_quota_text

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--M", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--p_max", type=float, default=0.16)
    ap.add_argument("--ev_slots_max", type=int, default=5)
    ap.add_argument("--fallback_max", type=int, default=5)
    ap.add_argument("--oversample_factor", type=int, default=40)
    ap.add_argument("--text", type=str, required=True)
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    quotas = parse_quota_text(args.text)

    # fill missing engines with 0
    engines = {}
    for k in ENGINE_KEYS:
        engines[k] = {"enabled": quotas.get(k, 0) > 0, "quota": int(quotas.get(k, 0))}

    # sum check
    s = sum(int(v["quota"]) for v in engines.values())
    if s != args.M:
        raise ValueError(f"[CONTRACT_FAIL] Sum(quota) must equal M. Sum={s}, M={args.M}")

    constitution = {
        "p_max": float(args.p_max),
        "ev_slots_max": int(args.ev_slots_max),
        "fallback_max": int(args.fallback_max),
        "oversample_factor": int(args.oversample_factor),
    }
    assert_constitution(constitution)

    selection = {
        "round": int(args.round),
        "M": int(args.M),
        "seed": int(args.seed),
        "ssot_sorted_path": "data/ssot_sorted.csv",
        "engines": engines,
        "constitution": constitution,
    }

    # contract validate keys
    assert_engine_keys_map({k:1 for k in engines.keys()})

    out = args.out or f"docs/reports/latest/ENGINE_SELECTION_R{args.round}_M{args.M}.json"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(selection, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] Wrote strategy: {out}")

if __name__ == "__main__":
    main()
