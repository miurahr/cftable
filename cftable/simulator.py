import csv
from typing import List, Dict, Any, Optional
from cftable.models import Member, IncomeEntry, ExpenseEntry
from cftable.account import Account

class Simulator:
    def __init__(self, settings: Dict[str, Any], members: List[Member], 
                 income_entries: List[IncomeEntry], expense_entries: List[ExpenseEntry], 
                 accounts: List[Account]):
        self.inflation_rate = settings['inflation_rate']
        self.duration_years = settings['duration_years']
        self.start_year = settings['start_year']
        self.members = members
        self.income_entries = income_entries
        self.expense_entries = expense_entries
        self.accounts = {a.name: a for a in accounts}
        self.results = []

    def run(self):
        for i in range(self.duration_years):
            current_year = self.start_year + i
            
            # 1. Apply returns to accounts
            for account in self.accounts.values():
                account.apply_return()

            # 2. Calculate Income
            annual_income = 0.0
            for entry in self.income_entries:
                annual_income += entry.get_amount(current_year)

            # 3. Calculate Expenses
            annual_expense = 0.0
            for entry in self.expense_entries:
                annual_expense += entry.get_amount(current_year, self.start_year, self.inflation_rate)

            # 4. Cash Flow to Living Account
            living_acc = self.accounts.get('living')
            if not living_acc:
                living_acc = Account('living', 0, 0)
                self.accounts['living'] = living_acc

            living_acc.balance += (annual_income - annual_expense)

            # 4.5. Maintain Defense Reserve (0.5 to 1.0 year of expenses)
            # Ensure defense has at least 6 months worth of annual expenses if living has surplus
            defense_accs = [acc for name, acc in self.accounts.items() if 'defense' in name.lower()]
            if defense_accs and living_acc.balance > 0:
                defense_acc = defense_accs[0]
                target_reserve = annual_expense * 0.5  # 6 months as recommended
                if defense_acc.balance < target_reserve:
                    needed = target_reserve - defense_acc.balance
                    transfer = min(needed, living_acc.balance)
                    defense_acc.balance += transfer
                    living_acc.balance -= transfer

            # 5. Withdrawal Strategies
            for name, acc in self.accounts.items():
                if name == 'living': continue
                if acc.withdrawal_strategy:
                    strat = acc.withdrawal_strategy
                    start_age = strat.get('start_age', 0)
                    
                    primary_member = next((m for m in self.members if m.role == 'self'), self.members[0])
                    if primary_member.get_age(current_year) >= start_age:
                        withdrawal_amount = 0.0
                        if strat['type'] == 'fixed_amount':
                            withdrawal_amount = strat['amount']
                        elif strat['type'] == 'fixed_rate':
                            withdrawal_amount = acc.balance * strat['rate']
                        
                        actual = acc.withdraw(withdrawal_amount)
                        living_acc.balance += actual

            # 6. Funding Logic if living < 0
            if living_acc.balance < 0:
                shortfall = -living_acc.balance
                
                def get_accounts_by_pattern(pattern):
                    return [acc for name, acc in self.accounts.items() if pattern in name.lower()]

                # 1. Defense (Emergency Fund) - prioritized as per user request
                for defense_acc in get_accounts_by_pattern('defense'):
                    if shortfall <= 0: break
                    withdrawn = defense_acc.withdraw(shortfall)
                    living_acc.balance += withdrawn
                    shortfall -= withdrawn

                # 2 & 3: General Account
                for general_acc in get_accounts_by_pattern('general'):
                    if shortfall <= 0: break
                    if general_acc.balance > 0:
                        cash_pos = general_acc.balance * general_acc.cash_ratio
                        sec_pos = general_acc.balance * (1 - general_acc.cash_ratio)
                        
                        from_cash = min(cash_pos, shortfall)
                        general_acc.balance -= from_cash
                        living_acc.balance += from_cash
                        shortfall -= from_cash
                        
                        if shortfall > 0:
                            from_sec = min(sec_pos, shortfall)
                            general_acc.balance -= from_sec
                            living_acc.balance += from_sec
                            shortfall -= from_sec

                # 4 & 5: NISA
                nisa_accounts = get_accounts_by_pattern('nisa')
                def nisa_priority(acc):
                    name = acc.name.lower()
                    if 'growth' in name or '成長' in name: return 0
                    if 'accum' in name or 'つみたて' in name or '積立' in name: return 1
                    return 2
                
                for nisa_acc in sorted(nisa_accounts, key=nisa_priority):
                    if shortfall <= 0: break
                    withdrawn = nisa_acc.withdraw(shortfall)
                    living_acc.balance += withdrawn
                    shortfall -= withdrawn

                # 6. DC / iDeCo
                if shortfall > 0:
                    dc_accounts = get_accounts_by_pattern('dc') + get_accounts_by_pattern('ideco')
                    for dc_acc in dc_accounts:
                        if shortfall <= 0: break
                        primary_member = next((m for m in self.members if m.role == 'self'), self.members[0])
                        if primary_member.get_age(current_year) >= 60:
                            withdrawn = dc_acc.withdraw(shortfall)
                            living_acc.balance += withdrawn
                            shortfall -= withdrawn

            # Record results
            year_result = {
                'year': current_year,
                'income': round(annual_income),
                'expense': round(annual_expense),
                'cash_flow': round(annual_income - annual_expense),
                'living_balance': round(living_acc.balance)
            }
            total_assets = 0.0
            for name, acc in self.accounts.items():
                year_result[f'{name}_balance'] = round(acc.balance)
                total_assets += acc.balance
            year_result['total_assets'] = round(total_assets)
            
            for m in self.members:
                year_result[f'{m.name}_age'] = m.get_age(current_year)

            self.results.append(year_result)

    def print_summary(self):
        if not self.results:
            print("No results to display.")
            return
        
        start_res = self.results[0]
        end_res = self.results[-1]
        
        print("\n=== Simulation Summary ===")
        print(f"Period: {start_res['year']} - {end_res['year']} ({len(self.results)} years)")
        print(f"Initial Assets: {start_res['total_assets']:,} JPY")
        print(f"Final Assets:   {end_res['total_assets']:,} JPY")
        
        min_assets_res = min(self.results, key=lambda x: x['total_assets'])
        print(f"Minimum Assets: {min_assets_res['total_assets']:,} JPY (at year {min_assets_res['year']})")
        
        if end_res['total_assets'] < 0:
            print("Warning: The simulation ends with negative assets.")
        print("==========================\n")

    def write_csv(self, output_path: str):
        if not self.results:
            return
        
        fieldnames = self.results[0].keys()
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)
