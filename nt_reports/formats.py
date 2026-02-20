import pandas as pd
import json

def validate_predictions_csv(df: pd.DataFrame):
    required = ["round", "engine_id", "mode", "combo_rank", "n1", "n2", "n3", "n4", "n5", "n6"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required prediction column: {col}")

def validate_performance_history_line(obj: dict):
    required = ["round", "timestamp", "summary"]
    for key in required:
        if key not in obj:
            raise ValueError(f"Missing required history key: {key}")

def validate_learning_log_line(obj: dict):
    required = ["timestamp", "module_id", "message"]
    for key in required:
        if key not in obj:
            raise ValueError(f"Missing required log key: {key}")
