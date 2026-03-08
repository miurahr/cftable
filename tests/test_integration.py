import os
import csv
import yaml
import pytest
from cftable.cli import run_cli
from unittest.mock import patch
import sys

def create_input_yaml(path, birth_date):
    data = {
        'simulation_settings': {
            'inflation_rate': 0.01,
            'duration_years': 30,
            'start_year': 2026
        },
        'members': [
            {
                'name': '本人',
                'role': 'self',
                'birth_date': birth_date,
                'retirement_age': 65,
                'pension_start_age': 65
            }
        ],
        'income_entries': [
            {
                'member': '本人',
                'category': 'salary',
                'amount': 5000000,
                'start_year': 2026,
                'end_year': 2040,
                'growth_rate': 0.01
            }
        ],
        'expense_entries': [
            {
                'category': 'living_expense',
                'amount': 3000000,
                'start_year': 2026,
                'end_year': 2055,
                'inflation_indexed': True
            }
        ],
        'accounts': [
            {
                'name': 'living',
                'initial_balance': 1000000,
                'expected_return': 0.0
            }
        ]
    }
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True)

@pytest.mark.parametrize("birth_year, expected_start_age", [
    (1981, 45),  # 2026 - 1981 = 45
    (1971, 55),  # 2026 - 1971 = 55
])
def test_integration_age_variations(tmp_path, birth_year, expected_start_age):
    input_path = tmp_path / f"input_{expected_start_age}.yaml"
    output_path = tmp_path / f"output_{expected_start_age}.csv"
    birth_date = f"{birth_year}-01-01"
    
    create_input_yaml(input_path, birth_date)
    
    # CLI実行をシミュレート
    test_args = ["cftable", str(input_path), "--output", str(output_path)]
    with patch.object(sys, 'argv', test_args):
        run_cli()
    
    # 出力CSVの存在確認
    assert os.path.exists(output_path)
    
    # CSVの内容確認
    with open(output_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        # 最初の年のデータを確認
        first_row = rows[0]
        assert int(first_row['year']) == 2026
        # CSVのヘッダー名を確認
        age_col = "本人_age"
        assert int(first_row[age_col]) == expected_start_age
        
        # 最終的な行数を確認 (duration_years = 30)
        assert len(rows) == 30
