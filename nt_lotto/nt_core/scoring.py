from typing import List, Tuple, Set, Dict, Any, Union
import pandas as pd
from nt_lotto.nt_core.types import ParsedWinning, ScoreRow

def parse_winning_input(ordered_six: Union[List[int], str], bonus: int) -> ParsedWinning:
    """
    Parse winning numbers input.
    """
    if isinstance(ordered_six, str):
        numbers = [int(x.strip()) for x in ordered_six.split(',')]
    else:
        numbers = list(ordered_six)

    if len(numbers) != 6:
        raise ValueError(f"Winning numbers must be 6, got {len(numbers)}")

    return {
        "win_set": set(numbers),
        "bonus": int(bonus)
    }

def score_combo(numbers: List[int], win_set: Set[int], bonus: int) -> Dict[str, Any]:
    """
    Score a single combination.
    Rank Rules:
    - 6 hits: 1st
    - 5 hits + bonus: 2nd
    - 5 hits: 3rd
    - 4 hits: 4th
    - 3 hits: 5th
    - Else: Fail (0)
    """
    matches = win_set.intersection(set(numbers))
    hits = len(matches)
    bonus_hit = bonus in numbers
    
    rank = 0
    if hits == 6:
        rank = 1
    elif hits == 5 and bonus_hit:
        rank = 2
    elif hits == 5:
        rank = 3
    elif hits == 4:
        rank = 4
    elif hits == 3:
        rank = 5
        
    return {
        "hits": hits,
        "matched": sorted(list(matches)),
        "bonus_hit": bonus_hit,
        "rank": rank
    }

def score_portfolio(round_no: int, portfolio: pd.DataFrame, ordered_six: Union[List[int], str], bonus: int) -> pd.DataFrame:
    """
    Score the entire portfolio dataframe.
    Input DF columns expected: "engine", "numbers" (string list "[1, 2, 3]")
    """
    winning = parse_winning_input(ordered_six, bonus)
    win_set = winning['win_set']
    bonus_val = winning['bonus']
    
    results = []
    
    for _, row in portfolio.iterrows():
        # Parse numbers from string like "[1, 2, 3]" or list
        nums_val = row['numbers']
        if isinstance(nums_val, str):
            # Safe eval or simple strip
            import ast
            try:
                numbers = ast.literal_eval(nums_val)
            except:
                numbers = [int(x) for x in nums_val.strip('[]').split(',')]
        else:
            numbers = list(nums_val)
            
        score_res = score_combo(numbers, win_set, bonus_val)
        
        # Build result row
        res_row = {
            "round": round_no,
            "engine": row['engine'],
            "numbers": sorted(numbers),
            "hits": score_res['hits'],
            "bonus_hit": score_res['bonus_hit'],
            "rank": score_res['rank'],
            "matched": score_res['matched']
        }
        results.append(res_row)
        
    return pd.DataFrame(results)

def summarize_scoreboard(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize scoreboard by engine.
    Counts of Rank 1..5
    """
    if df.empty:
        return pd.DataFrame()
        
    summary = []
    engines = df['engine'].unique()
    
    for eng in engines:
        sub = df[df['engine'] == eng]
        row = {"engine": eng, "total_combos": len(sub)}
        for r in range(1, 6):
            count = len(sub[sub['rank'] == r])
            row[f"rank{r}"] = count
        summary.append(row)
        
    return pd.DataFrame(summary)
