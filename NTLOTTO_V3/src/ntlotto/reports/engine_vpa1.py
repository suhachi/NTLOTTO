from __future__ import annotations
import pandas as pd
from ..core.stats_basic import bands_profile

def build_eng_vpa1(df_s: pd.DataFrame, df_o: pd.DataFrame) -> str:
    lines = [
        "# 엔진 리포트: VPA-1 (시각적/구조적 밴드 패턴)",
        "VPA-1은 로또 용지에서의 기하학적 분포와 번호대(Band)의 군집 특성에 초점을 맞춥니다.",
        ""
    ]
    if len(df_s) == 0:
        lines.append("데이터가 부족합니다.")
        return "\n".join(lines)

    bp = bands_profile(df_s)
    lines.append("## 번호대 앵커 분석")
    for b, rt in bp.items():
        lines.append(f"- **{b} 밴드**: 평균 {rt:.2f}개 등장")

    lines.append("")
    lines.append("- VPA-1 조합은 보통 1~2개의 밴드를 '몰빵(Cluster)' 하거나 완전 '멸(Empty)'로 만드는 템플릿을 취합니다.")

    return "\n".join(lines)
