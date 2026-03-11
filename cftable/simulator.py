from typing import List, Dict, Any, Optional
from cftable.models import Member, IncomeEntry, ExpenseEntry
from cftable.account import Account

class Simulator:
    def __init__(self, settings: Dict[str, Any], members: List[Member], 
                 income_entries: List[IncomeEntry], expense_entries: List[ExpenseEntry], 
                 accounts: List[Account]):
        self.inflation_rate = settings['inflation_rate']
        self.start_year = settings['start_year']
        self.members = members
        self.income_entries = income_entries
        self.expense_entries = expense_entries
        self.accounts = {a.name: a for a in accounts}
        self.results = []

        # Calculate duration_years
        if 'duration_years' in settings:
            self.duration_years = settings['duration_years']
        elif 'end_age' in settings:
            primary_member = next((m for m in self.members if m.role == 'self'), self.members[0])
            birth_year = primary_member.birth_date.year
            end_year = birth_year + settings['end_age']
            self.duration_years = max(0, end_year - self.start_year + 1)
        else:
            # Default to 50 years if neither is specified
            self.duration_years = 50

        # Resolve years for all entries
        for entry in self.income_entries:
            entry.resolve_years(self.members, self.start_year, self.duration_years)
        for entry in self.expense_entries:
            entry.resolve_years(self.members, self.start_year, self.duration_years)
        for account in self.accounts.values():
            account.resolve_years(self.members, self.start_year, self.duration_years)

    def run(self):
        primary_member = next((m for m in self.members if m.role == 'self'), self.members[0])

        # 4. Cash Flow to Living Account
        living_acc = self.accounts.get('living')
        if not living_acc:
            living_acc = Account('living', 0, 0)
            self.accounts['living'] = living_acc

        # 4. All possible keys for year_result
        # These will be used to initialize year_result dictionary
        income_detail_keys = []
        for entry in self.income_entries:
            key = f'income_{entry.member}_{entry.category}'
            if key not in income_detail_keys:
                income_detail_keys.append(key)
        income_detail_keys.sort()
        
        account_withdrawal_keys = [f'{name}_withdrawal' for name in sorted(self.accounts.keys())]
        account_balance_keys = [f'{name}_balance' for name in sorted(self.accounts.keys())]
        member_age_keys = [f'{m.name}_age' for m in self.members]

        expense_detail_keys = []
        for entry in self.expense_entries:
            key = f'expense_{entry.category}'
            if key not in expense_detail_keys:
                expense_detail_keys.append(key)
        expense_detail_keys.sort()

        self.field_keys = ['year', 'income', 'expense', 'cash_flow', 'withdrawal', 'living_balance', 'total_assets'] + \
                          member_age_keys + account_balance_keys + account_withdrawal_keys + income_detail_keys + expense_detail_keys

        for i in range(self.duration_years):
            current_year = self.start_year + i
            # Reset annual limits for NISA etc.
            for account in self.accounts.values():
                account.reset_annual_limit()

            # 4. Calculate Income
            annual_income = 0.0
            income_details = {k: 0.0 for k in income_detail_keys}
            for entry in self.income_entries:
                amount = entry.get_amount(current_year)
                annual_income += amount
                key = f'income_{entry.member}_{entry.category}'
                income_details[key] += amount

            # 5. Calculate Expenses
            annual_expense = 0.0
            expense_details = {k: 0.0 for k in expense_detail_keys}
            for entry in self.expense_entries:
                amount = entry.get_amount(current_year, self.start_year, self.inflation_rate)
                annual_expense += amount
                key = f'expense_{entry.category}'
                expense_details[key] += amount

            # 6. Cash Flow to Living Account
            living_acc.balance += (annual_income - annual_expense)

            # --- Withdrawals (After income/expense) ---
            annual_withdrawals = {name: 0.0 for name in self.accounts.keys()}

            # 1. Scheduled Withdrawal Strategies
            for name, acc in self.accounts.items():
                if name == 'living': continue
                if acc.withdrawal_strategy:
                    strat = acc.withdrawal_strategy
                    
                    # Determine start and end years
                    start_year = strat.get('start_year', 0)
                    end_year = strat.get('end_year', 9999)
                    
                    if start_year <= current_year <= end_year:
                        withdrawal_amount = 0.0
                        if strat['type'] == 'fixed_amount':
                            withdrawal_amount = strat['amount']
                        elif strat['type'] == 'fixed_rate':
                            # Withdrawal is calculated based on balance BEFORE return
                            withdrawal_amount = acc.balance * strat['rate']
                        
                        apply_tax = 'tokutei' in name.lower()
                        actual = acc.withdraw(withdrawal_amount, apply_tax=apply_tax)
                        living_acc.balance += actual
                        annual_withdrawals[name] += actual

            # 2. Funding Logic if living < living_acc.initial_balance or living < 0
            shortfall = 0.0
            if living_acc.balance < living_acc.initial_balance:
                shortfall = living_acc.initial_balance - living_acc.balance
            elif living_acc.balance < 0:
                shortfall = -living_acc.balance
            
            if shortfall > 0:
                
                def get_accounts_by_pattern(pattern):
                    return [name for name in self.accounts.keys() if pattern in name.lower()]

                # 2.2 Tokutei Account
                for name in get_accounts_by_pattern('tokutei'):
                    if shortfall <= 0: break
                    tokutei_acc = self.accounts[name]
                    if tokutei_acc.balance > 0:
                        cost_basis_ratio = tokutei_acc.cost_basis / tokutei_acc.balance if tokutei_acc.balance > 0 else 1.0
                        tax_factor = 1.0 - 0.2 * (1.0 - cost_basis_ratio)
                        gross_needed = shortfall / tax_factor
                        
                        # Use withdraw method which applies tax and updates balance
                        withdrawn_net = tokutei_acc.withdraw(gross_needed, apply_tax=True)
                        living_acc.balance += withdrawn_net
                        annual_withdrawals[name] += withdrawn_net
                        shortfall -= withdrawn_net

                # 2.3 NISA
                nisa_account_names = get_accounts_by_pattern('nisa')
                def nisa_priority(name):
                    n_lower = name.lower()
                    if 'growth' in n_lower or '成長' in n_lower: return 0
                    if 'accum' in n_lower or 'つみたて' in n_lower or '積立' in n_lower: return 1
                    return 2

                for name in sorted(nisa_account_names, key=nisa_priority):
                    if shortfall <= 0: break
                    nisa_acc = self.accounts[name]
                    withdrawn = nisa_acc.withdraw(shortfall)
                    living_acc.balance += withdrawn
                    annual_withdrawals[name] += withdrawn
                    shortfall -= withdrawn

                # 2.4 DC / iDeCo
                if shortfall > 0:
                    dc_account_names = get_accounts_by_pattern('dc') + get_accounts_by_pattern('ideco')
                    for name in dc_account_names:
                        if shortfall <= 0: break
                        dc_acc = self.accounts[name]
                        if primary_member.get_age(current_year) >= 60:
                            withdrawn = dc_acc.withdraw(shortfall)
                            living_acc.balance += withdrawn
                            annual_withdrawals[name] += withdrawn
                            shortfall -= withdrawn

            # 3. Apply returns to accounts (After withdrawals)
            for account in self.accounts.values():
                account.apply_return()

            surplus = max(0.0, living_acc.balance - living_acc.initial_balance)

            # 7. Surplus Investment
            # 7.1 DC/iDeCo Contributions
            dc_accounts = [acc for name, acc in self.accounts.items() if ('dc' in name.lower() or 'ideco' in name.lower())]
            for dc_acc in dc_accounts:
                if dc_acc.contribution_amount > 0 and surplus > 0:
                    if primary_member.get_age(current_year) < dc_acc.contribution_end_age:
                        amount = min(dc_acc.contribution_amount, surplus)
                        dc_acc.invest(amount)
                        living_acc.balance -= amount
                        surplus -= amount

            # 7.3 Investment of Surplus (NISA -> Tokutei)
            if surplus > 0:
                # 1. NISA investment
                nisa_accounts = [acc for name, acc in self.accounts.items() if 'nisa' in name.lower()]
                for nisa_acc in nisa_accounts:
                    if surplus <= 0: break
                    annual_room = nisa_acc.annual_investment_limit - nisa_acc.annual_invested
                    lifetime_room = nisa_acc.lifetime_investment_limit - nisa_acc.cost_basis
                    room = max(0.0, min(annual_room, lifetime_room))
                    if room > 0:
                        invest_amount = min(room, surplus)
                        nisa_acc.invest(invest_amount)
                        living_acc.balance -= invest_amount
                        surplus -= invest_amount

                # 2. Tokutei account investment
                if surplus > 0:
                    tokutei_accounts = [acc for name, acc in self.accounts.items() if 'tokutei' in name.lower()]
                    for tokutei_acc in tokutei_accounts:
                        if surplus <= 0: break
                        is_withdrawing = False
                        if tokutei_acc.withdrawal_strategy:
                            start_year = tokutei_acc.withdrawal_strategy.get('start_year', 0)
                            if current_year >= start_year:
                                is_withdrawing = True
                        if not is_withdrawing:
                            invest_amount = surplus
                            tokutei_acc.invest(invest_amount)
                            living_acc.balance -= invest_amount
                            surplus -= invest_amount

            # Record results
            year_result = {k: 0 for k in self.field_keys}
            year_result.update({
                'year': current_year,
                'income': round(annual_income),
                'withdrawal': round(sum(annual_withdrawals.values())),
                'expense': round(annual_expense),
                'cash_flow': round(annual_income - annual_expense),
                'living_balance': round(living_acc.balance)
            })
            for key, amount in income_details.items():
                year_result[key] = round(amount)
            
            for key, amount in expense_details.items():
                year_result[key] = round(amount)
            
            for name, withdrawal in annual_withdrawals.items():
                withdrawal_key = f'{name}_withdrawal'
                if withdrawal_key in self.field_keys:
                    year_result[withdrawal_key] = round(withdrawal)
            
            total_assets = 0.0
            dc_total_withdrawal = 0.0
            nisa_total_withdrawal = 0.0
            
            for name, acc in self.accounts.items():
                year_result[f'{name}_balance'] = round(acc.balance)
                total_assets += acc.balance
            
            for name, withdrawal in annual_withdrawals.items():
                withdrawal_key = f'{name}_withdrawal'
                if withdrawal_key in self.field_keys:
                    year_result[withdrawal_key] = round(withdrawal)
                
                if 'dc' in name.lower() or 'ideco' in name.lower():
                    dc_total_withdrawal += withdrawal
                elif 'nisa' in name.lower():
                    nisa_total_withdrawal += withdrawal

            year_result['total_assets'] = round(total_assets)
            
            for m in self.members:
                year_result[f'{m.name}_age'] = m.get_age(current_year)

            self.results.append(year_result)

        return self.results

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

