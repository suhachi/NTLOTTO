from __future__ import annotations

# required section headers (minimal hard lock)
WHY_LONG_SECTIONS = [
    "## 1. 기초 지표 (Foundation)",
    "## 2. 전이 지표 (Flow & Gap)",
    "## 3. 형태 지표 (Shape)",
    "## 4. 누적 지표 (Hot/Cold)",
]

WHY_SHORT_SECTIONS = [
    "## 1. Window별 핫 트렌드 변화",
    "## 2. 단기 vs 장기 모멘텀 (Surging)",
]

def assert_report_sections(text: str, required: list[str], name: str) -> None:
    for s in required:
        if s not in text:
            raise ValueError(f"[CONTRACT_FAIL] Report {name} missing section: {s}")
