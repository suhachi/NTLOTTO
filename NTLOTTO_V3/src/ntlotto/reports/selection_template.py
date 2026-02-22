from __future__ import annotations
import json
from ..core.report_writer import write_json

def write_selection_template(out_path: str) -> None:
    data = {"engine_selection":{}}
    engines = ["NT4", "NT5", "NT-Ω", "NTO", "NT-PAT", "NT-VPA-1", "NT-LL"]
    for e in engines:
        data["engine_selection"][e] = {
            "use": True,
            "weight": 1.0,
            "max_combos": 5
        }
    data["combo_generation_config"] = {
        "status": "DISABLED_BY_DEFAULT",
        "message": "Combination generation is not fully enabled. See README.md",
        "allow_uniqueness_check": True
    }
    write_json(out_path, data)
