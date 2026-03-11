import csv
from typing import List, Dict, Any

class CSVOutputWriter:
    def __init__(self, results: List[Dict[str, Any]]):
        self.results = results

    def write(self, output_path: str):
        if not self.results:
            return
        
        # Determine the column order
        first_res = self.results[0]
        keys = list(first_res.keys())
        
        # Group keys
        main_keys = ['year']
        # Age keys: {Member}_age
        age_keys = sorted([k for k in keys if k.endswith('_age')])
        # Summary keys
        summary_keys = ['income', 'expense', 'cash_flow', 'withdrawal', 'living_balance']
        # Balance keys: {Account}_balance (excluding living)
        balance_keys = sorted([k for k in keys if k.endswith('_balance') and k != 'living_balance'])
        # Total assets
        asset_keys = ['total_assets']
        # Detail keys: income_{Member}_{Category} and {Account}_withdrawal
        detail_keys = sorted([k for k in keys if k.startswith('income_') or k.endswith('_withdrawal')])
        
        fieldnames = main_keys + age_keys + summary_keys + balance_keys + asset_keys + detail_keys
        
        # Ensure all fieldnames actually exist in keys (to avoid errors if some are missing)
        fieldnames = [f for f in fieldnames if f in keys]
        
        # Add any keys that were missed (just in case)
        for k in keys:
            if k not in fieldnames:
                fieldnames.append(k)

        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)
