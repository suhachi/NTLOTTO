from __future__ import annotations

ENGINE_KEYS = ["NT4", "NT5", "NTO", "NT-Ω", "NT-VPA-1", "NT-LL", "NT-PAT"]

def assert_engine_key(k: str) -> None:
    if k not in ENGINE_KEYS:
        raise ValueError(f"[CONTRACT_FAIL] Unknown engine key: {k}. Allowed={ENGINE_KEYS}")

def assert_engine_keys_map(d: dict) -> None:
    for k in d.keys():
        assert_engine_key(k)
