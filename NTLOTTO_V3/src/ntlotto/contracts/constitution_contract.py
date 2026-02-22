from __future__ import annotations
import math

def cap_from(M: int, p_max: float) -> int:
    return int(math.ceil(M * p_max))

def assert_constitution(cfg: dict) -> None:
    # required keys with defaults allowed
    p_max = float(cfg.get("p_max", 0.16))
    if not (0.10 <= p_max <= 0.25):
        raise ValueError(f"[CONTRACT_FAIL] p_max out of safe range: {p_max}")

    ev_slots_max = int(cfg.get("ev_slots_max", 5))
    if ev_slots_max < 0 or ev_slots_max > 10:
        raise ValueError(f"[CONTRACT_FAIL] ev_slots_max invalid: {ev_slots_max}")

    fallback_max = int(cfg.get("fallback_max", 5))
    if fallback_max < 0 or fallback_max > 10:
        raise ValueError(f"[CONTRACT_FAIL] fallback_max invalid: {fallback_max}")

    oversample_factor = int(cfg.get("oversample_factor", 40))
    if oversample_factor < 10 or oversample_factor > 200:
        raise ValueError(f"[CONTRACT_FAIL] oversample_factor invalid: {oversample_factor}")
