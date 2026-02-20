import json
import os
import sys

def generate_allocation_reports():
    base_dir = "docs/reports/latest"
    eval_file = os.path.join(base_dir, "Engine_Evaluation_K20_N100.json")
    
    if not os.path.exists(eval_file):
        print(f"Error: {eval_file} not found.")
        return
        
    with open(eval_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    per_engine = data.get("per_engine", {})
    
    # Extract stats
    stats = []
    for en, metrics in per_engine.items():
        if en in ["NT-EXP", "NT-DPP", "NT-HCE", "NT-PAT", "AL1", "AL2", "ALX", "NT-Omega"]:
            # Exclude stubs and Omega itself for allocation decision of underlying engines if needed, 
            # but request said "to distribute weights". Omega isn't distributed.
            if en == "NT-Omega":
                pass # usually Omega is the final output, but user said "NT-Omega" in JSON example for recommendation. Let's include everything with baseline.
                
        # Some engines might have missing stats
        if "recall_all" not in metrics: continue
        
        recall_mean = metrics["recall_all"].get("mean", 0)
        recall_std = metrics["recall_all"].get("std", 0)
        recall_recent = metrics["recall_recent"].get("mean", 0)
        recall_past = metrics["recall_past"].get("mean", 0)
        stability = metrics["stability"].get("mean", 0)
        bonus_hit = metrics["bonus_hit"].get("mean", 0)
        
        drift = recall_recent - recall_past
        
        stats.append({
            "engine": en,
            "recall_mean": recall_mean,
            "recall_std": recall_std,
            "recall_recent": recall_recent,
            "recall_past": recall_past,
            "stability": stability,
            "bonus_hit_mean": bonus_hit,
            "drift": drift
        })
        
    # Sort by recall mean desc
    stats.sort(key=lambda x: x["recall_mean"], reverse=True)
    
    # Grading
    a_engines = []
    b_engines = []
    c_engines = []
    
    # For relative ranking (top 2, bottom 2)
    # Exclude stubs/diagnostic to make ranks meaningful? Actually let's include all evaluated ones that have scores > 0
    active_stats = [s for s in stats if s["recall_mean"] > 0]
    
    for i, s in enumerate(active_stats):
        en = s["engine"]
        is_top_2 = i < 2
        is_bottom_2 = i >= len(active_stats) - 2 and len(active_stats) > 4
        
        # Rules:
        # A등급: recall_mean이 전체 상위 2개 이내 AND stability>=0.70 AND drift>=-0.10
        # C등급: recall_mean이 하위 2개 이내 OR stability<0.60 OR drift<=-0.25
        # 나머지 B등급
        
        if is_top_2 and s["stability"] >= 0.70 and s["drift"] >= -0.10:
            grade = "A"
            a_engines.append(en)
        elif is_bottom_2 or s["stability"] < 0.60 or s["drift"] <= -0.25:
            grade = "C"
            c_engines.append(en)
        else:
            grade = "B"
            b_engines.append(en)
            
        s["grade"] = grade
        
    # Recommendation JSON
    rec_json = {
        "metadata": {
            "notice": "This is a proposed allocation based on N=100 evaluation. Not finalized.",
            "strategy": "A grade: 60~70%, B grade: 25~35%, C grade: 0~10%"
        },
        "proposed_allocation": {}
    }
    
    # Apportioning (Rough draft)
    # Let's say A=65%, B=30%, C=5% total. Split evenly among engines in that grade.
    a_share = 0.65 if len(a_engines) > 0 else 0
    b_share = 0.30 if len(b_engines) > 0 else 0
    c_share = 0.05 if len(c_engines) > 0 else 0
    
    # Adjust if some grades are empty
    total_share = a_share + b_share + c_share
    if total_share > 0:
        a_share /= total_share
        b_share /= total_share
        c_share /= total_share
    
    for s in active_stats:
        en = s["engine"]
        g = s["grade"]
        if g == "A":
            rec_json["proposed_allocation"][en] = round(a_share / len(a_engines), 3)
        elif g == "B":
            rec_json["proposed_allocation"][en] = round(b_share / len(b_engines), 3)
        elif g == "C":
            rec_json["proposed_allocation"][en] = round(c_share / len(c_engines), 3)
            
    # MD Sheet
    md_lines = [
        "# Allocation Decision Sheet",
        "**Purpose:** Provide data-driven evaluation to allocate resources combinations/budget.",
        "## Grading Criteria",
        "- **A Class (Increase):** `recall_mean` is in top 2 AND `stability` >= 0.70 AND `drift` >= -0.10",
        "- **C Class (Decrease):** `recall_mean` is in bottom 2 OR `stability` < 0.60 OR `drift` <= -0.25",
        "- **B Class (Maintain):** All other engines.",
        "",
        "## Engine Performance Overview",
        "| Engine | Grade | Recall Mean | Std | Stability | Drift(Rec-Past) | Bonus Hit |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]
    
    for s in active_stats:
        drift_str = f"{s['drift']:+.2f}"
        md_lines.append(f"| {s['engine']} | **{s['grade']}** | {s['recall_mean']:.2f} | {s['recall_std']:.2f} | {s['stability']:.2f} | {drift_str} | {s['bonus_hit_mean']:.2f} |")
        
    with open(os.path.join(base_dir, "Allocation_Decision_Sheet.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    with open(os.path.join(base_dir, "Allocation_Recommendation.json"), "w", encoding="utf-8") as f:
        json.dump(rec_json, f, indent=2, ensure_ascii=False)
        
    print("Allocation reports generated.")

if __name__ == "__main__":
    generate_allocation_reports()
