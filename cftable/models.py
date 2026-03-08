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
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    start_age: Optional[int] = None
    end_age: Optional[int] = None
    growth_rate: float = 0.0
    repeat_interval: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            member=data['member'],
            category=data['category'],
            amount=float(data['amount']),
            start_year=data.get('start_year') or data.get('year'),
            end_year=data.get('end_year'),
            start_age=data.get('start_age'),
            end_age=data.get('end_age'),
            growth_rate=data.get('growth_rate', 0.0),
            repeat_interval=data.get('repeat_interval')
        )

    def resolve_years(self, members: List[Member], default_start_year: int, default_duration: int):
        member_obj = next((m for m in members if m.name == self.member), None)
        if not member_obj:
            # If member not found, we can't resolve ages. 
            # Fallback to year fields or defaults.
            if self.start_year is None:
                self.start_year = default_start_year
            if self.end_year is None:
                self.end_year = self.start_year
            return

        birth_year = member_obj.birth_date.year
        if self.start_age is not None:
            self.start_year = birth_year + self.start_age
        elif self.start_year is None:
            self.start_year = default_start_year

        if self.end_age is not None:
            self.end_year = birth_year + self.end_age
        elif self.end_year is None:
            # If start_year was given as 'year' (one-shot), end_year should be same.
            # If start_year was None, it's also same.
            self.end_year = self.start_year

    def get_amount(self, current_year: int) -> float:
        if self.start_year is not None and self.end_year is not None:
            if self.start_year <= current_year <= self.end_year:
                # If it's a recurring entry, check if it matches the pattern
                if self.repeat_interval:
                    if (current_year - self.start_year) % self.repeat_interval != 0:
                        return 0.0
                
                years_passed = current_year - self.start_year
                return self.amount * ((1 + self.growth_rate) ** years_passed)
        return 0.0

@dataclass
class ExpenseEntry:
    category: str
    amount: float
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    start_age: Optional[int] = None
    end_age: Optional[int] = None
    member: Optional[str] = None
    inflation_indexed: bool = True
    growth_rate: float = 0.0
    repeat_interval: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            category=data['category'],
            amount=float(data['amount']),
            start_year=data.get('start_year') or data.get('year'),
            end_year=data.get('end_year'),
            start_age=data.get('start_age'),
            end_age=data.get('end_age'),
            member=data.get('member'),
            inflation_indexed=data.get('inflation_indexed', True),
            growth_rate=data.get('growth_rate', 0.0),
            repeat_interval=data.get('repeat_interval')
        )

    def resolve_years(self, members: List[Member], default_start_year: int, default_duration: int):
        # Determine which member's age to use. If not specified, use 'self' (primary).
        target_member_name = self.member
        if not target_member_name:
            member_obj = next((m for m in members if m.role == 'self'), members[0])
        else:
            member_obj = next((m for m in members if m.name == target_member_name), None)

        if not member_obj:
            if self.start_year is None:
                self.start_year = default_start_year
            if self.end_year is None:
                self.end_year = self.start_year
            return

        birth_year = member_obj.birth_date.year
        if self.start_age is not None:
            self.start_year = birth_year + self.start_age
        elif self.start_year is None:
            self.start_year = default_start_year

        if self.end_age is not None:
            self.end_year = birth_year + self.end_age
        elif self.end_year is None:
            self.end_year = self.start_year

    def get_amount(self, current_year: int, sim_start_year: int, inflation_rate: float) -> float:
        if self.start_year is not None and self.end_year is not None:
            if self.start_year <= current_year <= self.end_year:
                # If it's a recurring entry, check if it matches the pattern
                if self.repeat_interval:
                    if (current_year - self.start_year) % self.repeat_interval != 0:
                        return 0.0

                # Growth rate is applied relative to entry's own start_year
                years_passed = current_year - self.start_year
                amount = self.amount * ((1 + self.growth_rate) ** years_passed)
                
                if self.inflation_indexed:
                    # Inflation is applied relative to simulation start_year
                    sim_years_passed = current_year - sim_start_year
                    amount *= ((1 + inflation_rate) ** sim_years_passed)
                return amount
        return 0.0
