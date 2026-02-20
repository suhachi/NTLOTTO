import os
import sys
import pandas as pd
import logging

# Adjust path to find nt_lotto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from nt_lotto.nt_core.constants import SSOT_SORTED, SSOT_ORDERED

# Logging setup
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("ImportMD")

RAW_HISTORY_DIR = os.path.join(os.path.dirname(__file__), '../../data/raw_history')
MD_SORTED_FILE = os.path.join(RAW_HISTORY_DIR, '로또-회차별-당첨번호.md')
MD_ORDERED_FILE = os.path.join(RAW_HISTORY_DIR, '로또-추첨순서-데이터.md')

def parse_markdown_table(file_path):
    """
    Parses a markdown table into a list of dicts.
    Assumes standard pipe table format.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return []

    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Simple parser: skip lines until we find a table row
    # Header usually starts with |
    header_found = False
    headers = []
    
    for line in lines:
        line = line.strip()
        if not line.startswith('|'):
            continue
        
        # Check if separator line
        if '---' in line:
            continue
            
        cells = [c.strip() for c in line.split('|')]
        # usually first and last are empty if line starts/ends with |
        if cells and cells[0] == '': cells.pop(0)
        if cells and cells[-1] == '': cells.pop()
        
        if not header_found:
            headers = cells
            # Normalize headers? No, based on position is safer for now as encoding is messy
            header_found = True
            continue
            
        # Data row
        if len(cells) != len(headers):
            continue
            
        row_dict = {}
        for i, h in enumerate(headers):
            row_dict[i] = cells[i] # Use index as key to avoid encoding issues with header names
        data.append(row_dict)
            
    return data

def main():
    logger.info("Starting Import form MD Raw History...")
    
    # 1. Parse Sorted Data (Master for Date and Sorted Numbers)
    # Expected indices: 0=Year, 1=Round, 2=Date, 3..8=N1..N6, 9=Bonus
    sorted_rows = parse_markdown_table(MD_SORTED_FILE)
    logger.info(f"Parsed {len(sorted_rows)} rows from Sorted MD.")
    
    parsed_sorted = []
    for row in sorted_rows:
        try:
            # Flexible parsing: sometimes headers are different, but usually column order is fixed
            # Sorted MD: Year | Round | Date | N1 | N2 | N3 | N4 | N5 | N6 | Bonus
            r_val = int(row[1])
            date_val = row[2]
            n1 = int(row[3])
            n2 = int(row[4])
            n3 = int(row[5])
            n4 = int(row[6])
            n5 = int(row[7])
            n6 = int(row[8])
            bonus = int(row[9])
            
            parsed_sorted.append({
                'round': r_val,
                'date': date_val,
                'n1': n1, 'n2': n2, 'n3': n3, 'n4': n4, 'n5': n5, 'n6': n6,
                'bonus': bonus
            })
        except (ValueError, IndexError) as e:
            # logger.warn(f"Skipping row {row}: {e}")
            continue

    df_sorted_new = pd.DataFrame(parsed_sorted)
    
    # 2. Parse Ordered Data (For Draw Order)
    # Expected indices: 0=Round, 1..6=B1..B6, 7=Bonus
    ordered_rows = parse_markdown_table(MD_ORDERED_FILE)
    logger.info(f"Parsed {len(ordered_rows)} rows from Ordered MD.")
    
    parsed_ordered = []
    for row in ordered_rows:
        try:
            # Ordered MD: Round | B1 | B2 | B3 | B4 | B5 | B6 | Bonus
            r_val = int(row[0])
            b1 = int(row[1])
            b2 = int(row[2])
            b3 = int(row[3])
            b4 = int(row[4])
            b5 = int(row[5])
            b6 = int(row[6])
            # Bonus is also there, verify?
            
            parsed_ordered.append({
                'round': r_val,
                'b1': b1, 'b2': b2, 'b3': b3, 'b4': b4, 'b5': b5, 'b6': b6
                # Bonus and Date will be merged from Sorted
            })
        except (ValueError, IndexError):
            continue
            
    df_ordered_new = pd.DataFrame(parsed_ordered)
    
    # 3. Merge and Reconcile
    if df_sorted_new.empty or df_ordered_new.empty:
        logger.error("No data parsed. check MD files.")
        sys.exit(1)

    # Merge date and bonus from sorted to ordered
    # Left join on round
    merged_ordered = pd.merge(df_ordered_new, df_sorted_new[['round', 'date', 'bonus']], on='round', how='inner')
    
    # Re-order columns for Ordered SSOT
    # round,date,b1,b2,b3,b4,b5,b6,bonus
    df_ordered_final = merged_ordered[['round', 'date', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'bonus']].sort_values('round')
    
    # Re-order columns for Sorted SSOT
    # round,date,n1,n2,n3,n4,n5,n6,bonus
    df_sorted_final = df_sorted_new[['round', 'date', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'bonus']].sort_values('round')
    
    # 4. Save to CSV (Overwrite or Append? The user says "Add new round". Overwriting with full sorted set is safer for SSOT)
    # But wait, does MD contain ALL history? 
    # The snippet showed round 1208 down to 1193. It might be partial history.
    # If partial, we must merge with existing CSV.
    
    logger.info("Merging with existing SSOT Data...")
    
    if os.path.exists(SSOT_SORTED):
        old_sorted = pd.read_csv(SSOT_SORTED)
        combined_sorted = pd.concat([old_sorted, df_sorted_final]).drop_duplicates(subset=['round'], keep='last').sort_values('round')
    else:
        combined_sorted = df_sorted_final
        
    if os.path.exists(SSOT_ORDERED):
        old_ordered = pd.read_csv(SSOT_ORDERED)
        combined_ordered = pd.concat([old_ordered, df_ordered_final]).drop_duplicates(subset=['round'], keep='last').sort_values('round')
    else:
        combined_ordered = df_ordered_final

    # 5. Write Check
    logger.info(f"Writing {len(combined_sorted)} rows to {SSOT_SORTED}")
    combined_sorted.to_csv(SSOT_SORTED, index=False)
    
    logger.info(f"Writing {len(combined_ordered)} rows to {SSOT_ORDERED}")
    combined_ordered.to_csv(SSOT_ORDERED, index=False)
    
    logger.info("Import Complete.")

if __name__ == "__main__":
    main()
