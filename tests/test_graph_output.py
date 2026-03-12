import unittest
import os
from cftable.output import MatplotlibOutputWriter, MATPLOTLIB_AVAILABLE

class TestGraphOutput(unittest.TestCase):
    def test_matplotlib_output_writer(self):
        if not MATPLOTLIB_AVAILABLE:
            self.skipTest("matplotlib is not available")
            
        results = [
            {
                'year': 2026,
                '本人_age': 46,
                'income': 5000000,
                'expense': 3000000,
                'cash_flow': 2000000,
                'withdrawal': 0,
                'living_balance': 1000000,
                'total_assets': 6000000,
                'income_本人_salary': 5000000,
            },
            {
                'year': 2027,
                '本人_age': 47,
                'income': 5100000,
                'expense': 3100000,
                'cash_flow': 2000000,
                'withdrawal': 0,
                'living_balance': 3000000,
                'total_assets': 8000000,
                'income_本人_salary': 5100000,
            }
        ]
        writer = MatplotlibOutputWriter(results)
        output_path = 'test_graph_writer.png'
        try:
            writer.write(output_path)
            self.assertTrue(os.path.exists(output_path))
            self.assertGreater(os.path.getsize(output_path), 0)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

if __name__ == '__main__':
    unittest.main()
