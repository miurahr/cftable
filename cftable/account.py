from typing import Dict, Any, Optional

class Account:
    def __init__(self, name: str, initial_balance: float, expected_return: float, 
                 cash_ratio: float = 0.0, withdrawal_strategy: Optional[Dict[str, Any]] = None):
        self.name = name
        self.balance = float(initial_balance)
        self.expected_return = float(expected_return)
        self.cash_ratio = float(cash_ratio)
        self.withdrawal_strategy = withdrawal_strategy
        
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
