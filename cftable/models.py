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
        start_year = data.get('start_year')
        if start_year is None:
            # support 'year' as shortcut for one-shot payments
            start_year = data.get('year')
        
        if start_year is None:
            raise KeyError("Income entry must have 'start_year' or 'year'")
            
        end_year = data.get('end_year', start_year)
        
        return cls(
            member=data['member'],
            category=data['category'],
            amount=float(data['amount']),
            start_year=int(start_year),
            end_year=int(end_year),
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
        start_year = data.get('start_year')
        if start_year is None:
            # support 'year' as shortcut for one-shot payments
            start_year = data.get('year')
        
        if start_year is None:
            raise KeyError("Expense entry must have 'start_year' or 'year'")
            
        end_year = data.get('end_year', start_year)
        
        return cls(
            category=data['category'],
            amount=float(data['amount']),
            start_year=int(start_year),
            end_year=int(end_year),
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
