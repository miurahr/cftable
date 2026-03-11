import unittest
import os
from cftable.output import CSVOutputWriter

class TestOutput(unittest.TestCase):
    def test_csv_output_writer(self):
        results = [
            {
                'year': 2026,
                '本人_age': 46,
                'income': 5000000,
                'expense': 3000000,
                'cash_flow': 2000000,
                'withdrawal': 0,
                'living_balance': 1000000,
                'tokutei_balance': 5000000,
                'total_assets': 6000000,
                'income_本人_salary': 5000000,
                'tokutei_withdrawal': 0
            }
        ]
        writer = CSVOutputWriter(results)
        output_path = 'test_output_writer.csv'
        try:
            writer.write(output_path)
            self.assertTrue(os.path.exists(output_path))
            with open(output_path, 'r', encoding='utf-8-sig') as f:
                header = f.readline().strip()
                # Expected order: year, 本人_age, income, expense, cash_flow, withdrawal, living_balance, tokutei_balance, total_assets, income_本人_salary, tokutei_withdrawal
                expected_header = "year,本人_age,income,expense,cash_flow,withdrawal,living_balance,tokutei_balance,total_assets,income_本人_salary,tokutei_withdrawal"
                self.assertEqual(header, expected_header)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

if __name__ == '__main__':
    unittest.main()
