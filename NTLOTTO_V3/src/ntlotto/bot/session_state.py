from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

STATE_PATH = Path("docs/reports/latest/SESSION_STATE.json")

@dataclass
class SessionState:
    analyzed_up_to_round: Optional[int] = None
    report_round: Optional[int] = None           # 리포트 생성 대상 회차
    selection_path: Optional[str] = None         # 전략 파일 경로
    predicted_round: Optional[int] = None        # 조합 생성 대상 회차
    predicted_csv: Optional[str] = None          # 생성된 combos csv 경로

def load_state() -> SessionState:
    if not STATE_PATH.exists():
        return SessionState()
    obj = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return SessionState(**obj)

def save_state(st: SessionState) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(asdict(st), ensure_ascii=False, indent=2), encoding="utf-8")
