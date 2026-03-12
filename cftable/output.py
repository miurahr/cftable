import csv
import os
from typing import List, Dict, Any

from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableRow, TableCell
from odf.text import P

try:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import logging
    logging.getLogger('matplotlib.font_manager').disabled = True
    plt.rcParams['font.family'] = [
        'Noto Sans CJK JP',
        'Noto Sans JP',
        'Migu 1M',
        'IPAexGothic',
        'IPA Gothic',
        'Hiragino Sans',
        'MS Gothic',
        'DejaVu Sans',
        'Arial',
        'sans-serif'
    ]
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

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

class MatplotlibOutputWriter(BaseOutputWriter):
    def write(self, output_path: str):
        if not self.results:
            return
        
        if not MATPLOTLIB_AVAILABLE:
            print("matplotlib is not installed. Skipping graph generation.")
            return

        years = [r['year'] for r in self.results]
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Cash Flow Simulation Results', fontsize=16)

        # 1. Total assets per year (stacked bar)
        balance_keys = sorted([k for k in self.results[0].keys() if k.endswith('_balance')])
        balance_data = {k: [r.get(k, 0) for r in self.results] for k in balance_keys}
        
        bottom = [0.0] * len(years)
        for key in balance_keys:
            axes[0, 0].bar(years, balance_data[key], bottom=bottom, label=key.replace('_balance', ''))
            bottom = [b + v for b, v in zip(bottom, balance_data[key])]
        
        axes[0, 0].set_title('Total Assets per Year')
        axes[0, 0].set_ylabel('JPY')
        axes[0, 0].legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')
        axes[0, 0].grid(True, axis='y')
        axes[0, 0].yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

        # 2. Cash Flow per year
        cash_flow = [r['cash_flow'] for r in self.results]
        colors = ['green' if cf >= 0 else 'red' for cf in cash_flow]
        axes[0, 1].bar(years, cash_flow, color=colors)
        axes[0, 1].set_title('Annual Cash Flow')
        axes[0, 1].set_ylabel('JPY')
        axes[0, 1].grid(True, axis='y')
        axes[0, 1].yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

        # 3. Income details per year
        income_keys = sorted([k for k in self.results[0].keys() if k.startswith('income_')])
        income_data = {k: [r.get(k, 0) for r in self.results] for k in income_keys}
        
        bottom = [0.0] * len(years)
        for key in income_keys:
            axes[1, 0].bar(years, income_data[key], bottom=bottom, label=key.replace('income_', ''))
            bottom = [b + v for b, v in zip(bottom, income_data[key])]
        
        axes[1, 0].set_title('Income Details per Year')
        axes[1, 0].set_ylabel('JPY')
        axes[1, 0].legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')
        axes[1, 0].grid(True, axis='y')
        axes[1, 0].yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

        # 4. Expense details per year
        expense_keys = sorted([k for k in self.results[0].keys() if k.startswith('expense_')])
        expense_data = {k: [r.get(k, 0) for r in self.results] for k in expense_keys}
        
        if expense_keys:
            bottom = [0.0] * len(years)
            for key in expense_keys:
                axes[1, 1].bar(years, expense_data[key], bottom=bottom, label=key.replace('expense_', ''))
                bottom = [b + v for b, v in zip(bottom, expense_data[key])]
            
            axes[1, 1].legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')
        
        axes[1, 1].set_title('Expense Details per Year')
        axes[1, 1].grid(True, axis='y')
        axes[1, 1].yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(output_path)
        plt.close(fig)

def get_writer(output_path: str, results: List[Dict[str, Any]]):
    _, ext = os.path.splitext(output_path)
    ext = ext.lower()
    if ext == '.ods':
        return ODSOutputWriter(results)
    elif ext in ('.png', '.jpg', '.jpeg', '.pdf', '.svg'):
        return MatplotlibOutputWriter(results)
    else:
        return CSVOutputWriter(results)
