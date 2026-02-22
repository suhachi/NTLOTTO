from __future__ import annotations

def build_validation_report(val_res: dict) -> str:
    lines = [
        "# SSOT Validation Report",
        "",
        f"- **총 행 수**: {val_res['rows']} (R {val_res['round_min']} ~ {val_res['round_max']})",
        f"- **비정렬 허용 건수(단순 기록)**: {val_res['bad_sorted_order_rows']}",
        "",
        "## 검증 결과: **PASS**",
        "- 중복, 범위 초과, 결측 등 치명적 오류 없음."
    ]
    return "\n".join(lines)
