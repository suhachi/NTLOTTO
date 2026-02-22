from __future__ import annotations
import pandas as pd

def build_eng_nto(df_s: pd.DataFrame, df_o: pd.DataFrame) -> str:
    lines = [
        "# 엔진 리포트: NTO (혼합형 안정 시그널)",
        "NTO 엔진은 NT4의 장기 안정성과 오메가의 보완성을 적절히 융합하여 평균으로의 회귀를 노립니다.",
        ""
    ]
    if len(df_s) == 0:
        lines.append("데이터가 부족합니다.")
        return "\n".join(lines)

    lines.append("- NTO는 극단값을 배제(총합 너무 크거나 작음, 올 홀수/올 짝수 배제)합니다.")
    lines.append("- 중앙 지향적인 '안전한' 조합을 가장 많이 생성합니다.")

    return "\n".join(lines)
