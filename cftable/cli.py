import yaml
import argparse
import sys
from cftable.models import Member, IncomeEntry, ExpenseEntry
from cftable.account import Account
from cftable.simulator import Simulator

def run_cli():
    parser = argparse.ArgumentParser(description='Cash Flow Simulation Tool')
    parser.add_argument('input', help='Input YAML file path')
    parser.add_argument('--output', '-o', help='Output CSV file path', default='output.csv')
    
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML: {e}")
        sys.exit(1)

    settings = data['simulation_settings']
    members = [Member.from_dict(m) for m in data['members']]
    income_entries = [IncomeEntry.from_dict(i) for i in data['income_entries']]
    expense_entries = [ExpenseEntry.from_dict(e) for e in data['expense_entries']]
    accounts = [Account.from_dict(a) for a in data['accounts']]

    simulator = Simulator(settings, members, income_entries, expense_entries, accounts)
    simulator.run()
    simulator.print_summary()
    simulator.write_csv(args.output)
    
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    run_cli()
