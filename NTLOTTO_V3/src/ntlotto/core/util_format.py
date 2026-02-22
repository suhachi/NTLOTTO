from __future__ import annotations
from datetime import datetime

BANDS = ["1–9","10–19","20–29","30–39","40–45"]

def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def fmt_f(x: float, d: int = 2) -> str:
    return f"{x:.{d}f}"

def pct(x: float, d: int = 1) -> str:
    return f"{x*100:.{d}f}%"

def band_of(n: int) -> str:
    if 1 <= n <= 9: return "1–9"
    if 10 <= n <= 19: return "10–19"
    if 20 <= n <= 29: return "20–29"
    if 30 <= n <= 39: return "30–39"
    return "40–45"
