from .base import EngineBase, StubEngine
from typing import List

# Fixed list of engines
ENGINE_IDS = [
    "NT4", "NT-OMEGA", "NT5", "NTO", "NT-LL", "VPA", "NT-VPA-1", 
    "AL1", "AL2", "ALX", "NT-EXP", "NT-DPP", "NT-HCE", "NT-PAT"
]

def get_engines() -> List[EngineBase]:
    """
    Factory to return all registered engines.
    Currently returns Stubs for most.
    """
    engines = []
    
    # TODO: Replace Stubs with actual implementations as they are ported
    for eid in ENGINE_IDS:
        # AL series might need ordered data
        req_ssot = "both" if eid.startswith("AL") else "sorted"
        
        # Instantiate actual engine if available, else Stub
        # For now, all are stubs as per instruction to build scaffolding first
        # unless specific logic is requested.
        # User said "Do NOT modify engine scoring logic yet", so Stubs are appropriate
        # for preserving the interface.
        
        engines.append(StubEngine(eid, required_ssot=req_ssot))
        
    return engines
