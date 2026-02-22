from __future__ import annotations
from pathlib import Path
import json
from .util_format import now_stamp

def ensure_dirs(*paths: str) -> None:
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)

def write_text(path: str, content: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding="utf-8")

def write_json(path: str, obj: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def history_path(latest_path: str) -> str:
    p = Path(latest_path)
    stamp = now_stamp()
    # latest -> history
    if "docs/reports/latest" in str(p):
        hp = Path(str(p).replace("docs/reports/latest", "docs/reports/history"))
    else:
        hp = p
    return str(hp.with_name(f"{hp.stem}_{stamp}{hp.suffix}"))
