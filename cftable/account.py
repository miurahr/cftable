from typing import Dict, Any, Optional

class Account:
    def __init__(self, name: str, initial_balance: float, expected_return: float, 
                 cash_ratio: float = 0.0, withdrawal_strategy: Optional[Dict[str, Any]] = None,
                 initial_cost_basis: Optional[float] = None,
                 annual_investment_limit: float = 0.0, lifetime_investment_limit: float = 0.0,
                 contribution_amount: float = 0.0, contribution_end_age: int = 0):
        self.name = name
        self.balance = float(initial_balance)
        self.expected_return = float(expected_return)
        self.cash_ratio = float(cash_ratio)
        self.withdrawal_strategy = withdrawal_strategy
        # 投資元本（cost basis）を追跡するためのフィールド
        # 指定されない場合は初期残高を元本とする
        self.cost_basis = float(initial_cost_basis) if initial_cost_basis is not None else self.balance
        
        # NISA制限設定
        self.annual_investment_limit = float(annual_investment_limit)
        self.lifetime_investment_limit = float(lifetime_investment_limit)
        self.annual_invested = 0.0
        
        # DC/iDeCo 拠出設定
        self.contribution_amount = float(contribution_amount)
        self.contribution_end_age = int(contribution_end_age)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            name=data['name'],
            initial_balance=data['initial_balance'],
            expected_return=data.get('expected_return', 0.0),
            cash_ratio=data.get('cash_ratio', 0.0),
            withdrawal_strategy=data.get('withdrawal_strategy'),
            initial_cost_basis=data.get('initial_cost_basis'),
            annual_investment_limit=data.get('annual_investment_limit', 0.0),
            lifetime_investment_limit=data.get('lifetime_investment_limit', 0.0),
            contribution_amount=data.get('contribution_amount', 0.0),
            contribution_end_age=data.get('contribution_end_age', 0)
        )

    def apply_return(self):
        self.balance *= (1 + self.expected_return)

    def reset_annual_limit(self):
        self.annual_invested = 0.0

    def invest(self, amount: float) -> float:
        """指定された金額を投資し、実際に投資された金額を返す。
        NISA制限やDC拠出設定などは呼び出し側（Simulator）で考慮する。"""
        self.balance += amount
        self.cost_basis += amount
        self.annual_invested += amount
        return amount

    def withdraw(self, amount: float, apply_tax: bool = False) -> float:
        """
        指定された金額（グロス）を取り崩し、実際の手取り額を返す。
        apply_tax=True の場合、利益に対して20%の税金を差し引く。
        """
        if self.balance <= 0:
            return 0.0
            
        actual_withdrawal_gross = min(self.balance, amount)
        
        # 元本の按分計算
        ratio = actual_withdrawal_gross / self.balance
        withdrawn_cost_basis = self.cost_basis * ratio
        
        # 利益の計算
        profit = actual_withdrawal_gross - withdrawn_cost_basis
        
        tax = 0.0
        if apply_tax and profit > 0:
            tax = profit * 0.2
            
        self.balance -= actual_withdrawal_gross
        self.cost_basis -= withdrawn_cost_basis
        
        return actual_withdrawal_gross - tax
