import unittest
from datetime import datetime
from cftable.models import Member, IncomeEntry, ExpenseEntry
from cftable.simulator import Simulator
from cftable.account import Account

class TestAgeBasedEntries(unittest.TestCase):
    def setUp(self):
        self.settings = {
            'inflation_rate': 0.0,
            'start_year': 2026,
            'end_age': 100
        }
        self.members = [
            Member(name="本人", role="self", birth_date=datetime(1980, 1, 1), retirement_age=65, pension_start_age=65)
        ]

    def test_income_start_age(self):
        # 1980年生まれ、65歳は2045年
        income = [
            IncomeEntry(member="本人", category="pension", amount=1000000, start_age=65, end_age=70)
        ]
        sim = Simulator(self.settings, self.members, income, [], [])
        
        # 2044年 (64歳) は 0
        self.assertEqual(income[0].get_amount(2044), 0)
        # 2045年 (65歳) は 1000000
        self.assertEqual(income[0].get_amount(2045), 1000000)
        # 2050年 (70歳) は 1000000
        self.assertEqual(income[0].get_amount(2050), 1000000)
        # 2051年 (71歳) は 0
        self.assertEqual(income[0].get_amount(2051), 0)

    def test_expense_start_age(self):
        # 本人の年齢基準
        expense = [
            ExpenseEntry(category="medical", amount=500000, start_age=75, end_age=100)
        ]
        sim = Simulator(self.settings, self.members, [], expense, [])
        
        # 1980 + 75 = 2055
        self.assertEqual(expense[0].get_amount(2054, 2026, 0.0), 0)
        self.assertEqual(expense[0].get_amount(2055, 2026, 0.0), 500000)

    def test_expense_growth_rate(self):
        expense = [
            ExpenseEntry(category="test", amount=1000, start_year=2026, end_year=2030, growth_rate=0.1, inflation_indexed=False)
        ]
        # simulator will resolve years (start_year=2026 is already set)
        sim = Simulator(self.settings, self.members, [], expense, [])
        
        # 2026: 1000
        # 2027: 1000 * 1.1 = 1100
        self.assertEqual(expense[0].get_amount(2026, 2026, 0.0), 1000)
        self.assertEqual(expense[0].get_amount(2027, 2026, 0.0), 1100)

    def test_child_education_expense(self):
        # 2020年生まれの子供
        child = Member(name="子供", role="child", birth_date=datetime(2020, 1, 1), retirement_age=65, pension_start_age=65)
        members = self.members + [child]
        
        # 子供の6歳(2026年)から22歳(2042年)までの教育費
        expense = [
            ExpenseEntry(category="education", member="子供", amount=1000000, start_age=6, end_age=22, inflation_indexed=False)
        ]
        
        sim = Simulator(self.settings, members, [], expense, [])
        
        # 2025年 (5歳) は 0
        self.assertEqual(expense[0].get_amount(2025, 2026, 0.0), 0)
        # 2026年 (6歳) は 1000000
        self.assertEqual(expense[0].get_amount(2026, 2026, 0.0), 1000000)
        # 2042年 (22歳) は 1000000
        self.assertEqual(expense[0].get_amount(2042, 2026, 0.0), 1000000)
        # 2043年 (23歳) は 0
        self.assertEqual(expense[0].get_amount(2043, 2026, 0.0), 0)

if __name__ == '__main__':
    unittest.main()
