import csv
import os
from typing import List, Dict, Any

from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P

class BaseOutputWriter:
    def __init__(self, results: List[Dict[str, Any]]):
        self.results = results

    def get_fieldnames(self) -> List[str]:
        if not self.results:
            return []
        
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
        
        return fieldnames

class CSVOutputWriter(BaseOutputWriter):
    def write(self, output_path: str):
        if not self.results:
            return
        
        fieldnames = self.get_fieldnames()

        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)

class ODSOutputWriter(BaseOutputWriter):
    def write(self, output_path: str):
        if not self.results:
            return

        fieldnames = self.get_fieldnames()
        
        doc = OpenDocumentSpreadsheet()
        table = Table(name="CashFlow")
        doc.spreadsheet.addElement(table)
        
        # Header
        header_row = TableRow()
        for field in fieldnames:
            cell = TableCell()
            cell.addElement(P(text=field))
            header_row.addElement(cell)
        table.addElement(header_row)
        
        # Rows
        for result in self.results:
            row = TableRow()
            for field in fieldnames:
                val = result.get(field, "")
                cell = TableCell()
                # Determine value type if possible
                if isinstance(val, (int, float)):
                    if field == 'year' or field.endswith('_age'):
                        cell.setAttribute('valuetype', 'float')
                    else:
                        cell.setAttribute('valuetype', 'currency')
                        cell.setAttribute('currency', 'JPY')
                    cell.setAttribute('value', str(val))
                    cell.addElement(P(text=str(val)))
                else:
                    cell.setAttribute('valuetype', 'string')
                    cell.addElement(P(text=str(val)))
                row.addElement(cell)
            table.addElement(row)
            
        doc.save(output_path)

def get_writer(output_path: str, results: List[Dict[str, Any]]):
    _, ext = os.path.splitext(output_path)
    if ext.lower() == '.ods':
        return ODSOutputWriter(results)
    else:
        return CSVOutputWriter(results)
