from __future__ import annotations
import re
from ntlotto.contracts.engine_contract import assert_engine_key

def parse_quota_text(text: str) -> dict[str,int]:
    # Accept separators: / , ; | newline
    parts = re.split(r"[\/,\;\|\n]+", text)
    out: dict[str,int] = {}
    for p in parts:
        p = p.strip()
        if not p:
            continue
        m = re.match(r"^(NT4|NT5|NTO|NT-Ω|NT-VPA-1|NT-LL|NT-PAT)\s+(\d+)$", p)
        if not m:
            raise ValueError(f"[INPUT_FAIL] Invalid token: '{p}'. Expected: 'NT5 10' 형식")
        k = m.group(1)
        v = int(m.group(2))
        assert_engine_key(k)
        out[k] = v
    return out
