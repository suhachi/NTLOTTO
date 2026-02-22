from __future__ import annotations
import pandas as pd

def build_eng_ll(df_s: pd.DataFrame, df_o: pd.DataFrame) -> str:
    lines = [
        "# 엔진 리포트: LL (지엽적 흐름 포착)",
        "LL 엔진은 가장 최근 2~3회차에 나타나는 아주 미세하고 국소적인(Local) 변화량 변화(Drift)에 투자합니다.",
        ""
    ]
    if len(df_s) < 3:
        lines.append("데이터가 너무 부족하여 LL 분석이 불가능합니다.")
        return "\n".join(lines)

    lines.append("- **초단기 회귀 분석**: 직전 3차수 이내의 간극 증감을 모델링하여 다음 1회차에 투사합니다.")
    lines.append("- 리스크가 가장 높으나, 맞을 경우 소외된 패턴을 정확히 낚아챕니다.")

    return "\n".join(lines)
