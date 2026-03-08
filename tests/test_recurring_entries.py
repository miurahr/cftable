import unittest
from datetime import datetime
from cftable.models import Member, ExpenseEntry

class TestRecurringEntries(unittest.TestCase):
    def test_expense_recurring(self):
        # 15年おきの支出。2030年に開始、2060年に終了。
        # ヒットする年: 2030, 2045, 2060
        expense = ExpenseEntry(
            category="housing_maintenance",
            amount=500000,
            start_year=2030,
            end_year=2060,
            repeat_interval=15,
            inflation_indexed=False
        )
        
        # 2030: ヒット
        self.assertEqual(expense.get_amount(2030, 2026, 0.0), 500000)
        # 2031: ヒットしない
        self.assertEqual(expense.get_amount(2031, 2026, 0.0), 0)
        # 2044: ヒットしない
        self.assertEqual(expense.get_amount(2044, 2026, 0.0), 0)
        # 2045: ヒット
        self.assertEqual(expense.get_amount(2045, 2026, 0.0), 500000)
        # 2059: ヒットしない
        self.assertEqual(expense.get_amount(2059, 2026, 0.0), 0)
        # 2060: ヒット
        self.assertEqual(expense.get_amount(2060, 2026, 0.0), 500000)
        # 2061: 期間外
        self.assertEqual(expense.get_amount(2061, 2026, 0.0), 0)

if __name__ == '__main__':
    unittest.main()
