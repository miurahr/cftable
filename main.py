import yaml
import argparse
import csv
import sys
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Member:
    name: str
    role: str
    birth_date: datetime
    retirement_age: int
    pension_start_age: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            name=data['name'],
            role=data['role'],
            birth_date=datetime.strptime(data['birth_date'], '%Y-%m-%d'),
            retirement_age=data['retirement_age'],
            pension_start_age=data['pension_start_age']
        )

    def get_age(self, year: int) -> int:
        return year - self.birth_date.year

@dataclass
class IncomeEntry:
    member: str
    category: str
    amount: float
    start_year: int
    end_year: int
    growth_rate: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            member=data['member'],
            category=data['category'],
            amount=float(data['amount']),
            start_year=data['start_year'],
            end_year=data['end_year'],
            growth_rate=data.get('growth_rate', 0.0)
        )

    def get_amount(self, current_year: int) -> float:
        if self.start_year <= current_year <= self.end_year:
            years_passed = current_year - self.start_year
            return self.amount * ((1 + self.growth_rate) ** years_passed)
        return 0.0

@dataclass
class ExpenseEntry:
    category: str
    amount: float
    start_year: int
    end_year: int
    inflation_indexed: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            category=data['category'],
            amount=float(data['amount']),
            start_year=data['start_year'],
            end_year=data['end_year'],
            inflation_indexed=data.get('inflation_indexed', True)
        )

    def get_amount(self, current_year: int, start_year: int, inflation_rate: float) -> float:
        if self.start_year <= current_year <= self.end_year:
            if self.inflation_indexed:
                years_passed = current_year - start_year
                return self.amount * ((1 + inflation_rate) ** years_passed)
            else:
                return self.amount
        return 0.0

class Account:
    def __init__(self, name: str, initial_balance: float, expected_return: float, 
                 cash_ratio: float = 0.0, withdrawal_strategy: Optional[Dict[str, Any]] = None):
        self.name = name
        self.balance = float(initial_balance)
        self.expected_return = float(expected_return)
        self.cash_ratio = float(cash_ratio)
        self.withdrawal_strategy = withdrawal_strategy
        
        # For general account, we might want to track cash and securities separately
        # but the spec says "cash_ratio" is a ratio of the balance.
        # Actually, let's keep it simple for now and only split if it's "general".

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            name=data['name'],
            initial_balance=data['initial_balance'],
            expected_return=data.get('expected_return', 0.0),
            cash_ratio=data.get('cash_ratio', 0.0),
            withdrawal_strategy=data.get('withdrawal_strategy')
        )

    def apply_return(self):
        self.balance *= (1 + self.expected_return)

    def withdraw(self, amount: float) -> float:
        actual_withdrawal = min(self.balance, amount)
        self.balance -= actual_withdrawal
        return actual_withdrawal

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
            
            # 1. Apply returns to accounts (except living maybe? Spec says B_n = B_{n-1} * (1+i) + CF_n)
            # Actually B_n is year-end balance. CF_n is annual cash flow.
            # Let's assume returns are applied to the beginning balance.
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
                # Should not happen based on spec
                living_acc = Account('living', 0, 0)
                self.accounts['living'] = living_acc

            living_acc.balance += (annual_income - annual_expense)

            # 5. Withdrawal Strategies (e.g. from general to living)
            for name, acc in self.accounts.items():
                if name == 'living': continue
                if acc.withdrawal_strategy:
                    strat = acc.withdrawal_strategy
                    start_age = strat.get('start_age', 0)
                    
                    # Check if any member has reached the start_age (usually 'self')
                    # Spec says "特定の年齢や条件において". Let's assume it refers to the primary member ('self').
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
                
                # Priority:
                # 1. general (cash)
                # 2. general (securities)
                # 3. nisa (growth)
                # 4. nisa (accumulation)
                # 5. defense (not in 1-4 but is a liquidity account)
                # 6. dc / ideco (if age >= 60)
                
                # Helper to find accounts by name pattern
                def get_accounts_by_pattern(pattern):
                    return [acc for name, acc in self.accounts.items() if pattern in name.lower()]

                # 1 & 2: General Account
                for general_acc in get_accounts_by_pattern('general'):
                    if shortfall <= 0: break
                    if general_acc.balance > 0:
                        cash_pos = general_acc.balance * general_acc.cash_ratio
                        sec_pos = general_acc.balance * (1 - general_acc.cash_ratio)
                        
                        # 1. Withdraw from cash first
                        from_cash = min(cash_pos, shortfall)
                        general_acc.balance -= from_cash
                        living_acc.balance += from_cash
                        shortfall -= from_cash
                        
                        if shortfall > 0:
                            # 2. Then from securities
                            from_sec = min(sec_pos, shortfall)
                            general_acc.balance -= from_sec
                            living_acc.balance += from_sec
                            shortfall -= from_sec

                # 3 & 4: NISA
                # Search for growth specifically first, then accumulation, then general "nisa"
                nisa_accounts = get_accounts_by_pattern('nisa')
                # Sort by priority: growth > accumulation > others
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

                # 5. Defense
                if shortfall > 0:
                    for defense_acc in get_accounts_by_pattern('defense'):
                        if shortfall <= 0: break
                        withdrawn = defense_acc.withdraw(shortfall)
                        living_acc.balance += withdrawn
                        shortfall -= withdrawn

                # 6. DC / iDeCo (with age restriction, e.g., 60)
                if shortfall > 0:
                    dc_accounts = get_accounts_by_pattern('dc') + get_accounts_by_pattern('ideco')
                    for dc_acc in dc_accounts:
                        if shortfall <= 0: break
                        primary_member = next((m for m in self.members if m.role == 'self'), self.members[0])
                        if primary_member.get_age(current_year) >= 60:
                            withdrawn = dc_acc.withdraw(shortfall)
                            living_acc.balance += withdrawn
                            shortfall -= withdrawn

            # Record results (round to 0 decimal places for Yen)
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
            
            # Age of members
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
        
        # Find year with minimum assets
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

def main():
    parser = argparse.ArgumentParser(description='Cash Flow Simulation Tool')
    parser.add_argument('input', help='Input YAML file path')
    parser.add_argument('--output', '-o', help='Output CSV file path', default='output.csv')
    
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML: {e}")
        sys.exit(1)

    settings = data['simulation_settings']
    members = [Member.from_dict(m) for m in data['members']]
    income_entries = [IncomeEntry.from_dict(i) for i in data['income_entries']]
    expense_entries = [ExpenseEntry.from_dict(e) for e in data['expense_entries']]
    accounts = [Account.from_dict(a) for a in data['accounts']]

    simulator = Simulator(settings, members, income_entries, expense_entries, accounts)
    simulator.run()
    simulator.print_summary()
    simulator.write_csv(args.output)
    
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()
