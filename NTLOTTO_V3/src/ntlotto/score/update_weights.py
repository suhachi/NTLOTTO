from __future__ import annotations
import json
from ..core.report_writer import write_text, write_json

def update_weights(eval_results: dict, out_dir: str):
    """
    엔진 평가 결과를 바탕으로 가중치(NTO 등에서 쓰일)를 보수적으로 업데이트
    우위가 명확하지 않으면 동결
    """
    out = {}
    md_lines = ["# Weight Update Rationale", ""]
    
    # 단순 규칙: recall_mean이 0.25 (평균 1.5개) 이상이면 가중치 부여, 이하면 기본값 또는 동결
    for eng, stats in eval_results.items():
        rm = stats["recall_mean"]
        if rm > 0.25:
            weight = 1.2
            rationale = "Recall 우수 (우위 판독: 가중치 상향)"
        elif rm < 0.15:
            weight = 0.8
            rationale = "Recall 부진 (우위 판독: 가중치 하향)"
        else:
            weight = 1.0
            rationale = "통계적 우위 불명확 (동결)"
            
        out[eng] = {
            "weight": weight,
            "recall_mean": rm
        }
        md_lines.append(f"- **{eng}**: {rationale} (New Weight: {weight}, Recall: {rm:.3f})")
        
    write_json(f"{out_dir}/Weights_Updated.json", out)
    write_text(f"{out_dir}/Weights_Rationale.md", "\n".join(md_lines))
    print(f"[*] Weights updated conservatively. Saved to {out_dir}/Weights_Updated.json")
