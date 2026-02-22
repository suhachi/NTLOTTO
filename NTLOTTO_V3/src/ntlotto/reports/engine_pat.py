from __future__ import annotations
import pandas as pd
from ..core.stats_patterns import top_pairs

def build_eng_pat(df_s: pd.DataFrame, df_o: pd.DataFrame) -> str:
    lines = [
        "# 엔진 리포트: PAT (페어 및 앙상블 패턴)",
        "PAT 엔진은 자주 같이 나오는 쌍(Pair) 단위, 혹은 규칙적 삼각 패턴을 기반으로 전체 그림을 맞춥니다.",
        ""
    ]
    if len(df_s) == 0:
        lines.append("데이터가 부족합니다.")
        return "\n".join(lines)

    pairs = top_pairs(df_s, 5)
    lines.append("## Top 5 페어 세트")
    for (p1, p2), c in pairs:
        lines.append(f"- [{p1}, {p2}]: {c}회 동시 출현")

    lines.append("")
    lines.append("- PAT 엔진은 추출된 상위 페어 조합을 시드(Seed)로 하여 나머지 4자리를 확률적으로 스캐폴딩합니다.")

    return "\n".join(lines)
