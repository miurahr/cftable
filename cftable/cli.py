try:
    import yaml
except ImportError:
    # 実行環境にPyYAMLがない場合は、後続の処理でエラーになる
    pass

import argparse
import sys
from cftable.models import Member, IncomeEntry, ExpenseEntry
from cftable.account import Account
from cftable.simulator import Simulator
from cftable.output import get_writer

def check_privacy_concerns(data):
    """入力データに個人情報が含まれていそうな場合に警告を表示する"""
    members = data.get('members', [])
    if not members:
        return

    is_potentially_sensitive = False
    
    # サンプル名以外の名前が使われているかチェック
    sample_names = {"本人", "配偶者", "self", "spouse", "child", "子供", "子"}
    for m in members:
        name = m.get('name', "")
        if name and name not in sample_names:
            is_potentially_sensitive = True
            break
            
        # 生年月日がデフォルト（1980-01-01, 1982-05-15）以外かチェック
        # (厳密すぎると誤検知が多いが、変更されている=実データを入れた可能性が高い)
        birth_date = str(m.get('birth_date', ""))
        if birth_date and birth_date not in {"1980-01-01", "1982-05-15"}:
            is_potentially_sensitive = True
            break

    if is_potentially_sensitive:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", file=sys.stderr)
        print("WARNING: この入力ファイルには個人情報が含まれている可能性があります。", file=sys.stderr)
        print("fork したリポジトリや公開ブランチにこのファイルをコミットしないよう注意してください。", file=sys.stderr)
        print("個人用ファイルには `*.local.yaml` のようなローカルファイル名を推奨します。", file=sys.stderr)
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", file=sys.stderr)
        print("", file=sys.stderr)

def run_cli():
    parser = argparse.ArgumentParser(description='Cash Flow Simulation Tool')
    parser.add_argument('input', help='Input YAML file path')
    parser.add_argument('--output', '-o', help='Output CSV file path', default='output.csv')
    parser.add_argument('--graph', '-g', help='Output graph image path (e.g., graph.png)')
    
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            check_privacy_concerns(data)
    except Exception as e:
        print(f"Error loading YAML: {e}")
        sys.exit(1)

    settings = data['simulation_settings']
    members = [Member.from_dict(m) for m in data['members']]
    income_entries = [IncomeEntry.from_dict(i) for i in data['income_entries']]
    expense_entries = [ExpenseEntry.from_dict(e) for e in data['expense_entries']]
    accounts = [Account.from_dict(a) for a in data['accounts']]

    simulator = Simulator(settings, members, income_entries, expense_entries, accounts)
    results = simulator.run()
    simulator.print_summary()
    
    writer = get_writer(args.output, results)
    writer.write(args.output)
    print(f"Results saved to: {args.output}")

    if args.graph:
        graph_writer = get_writer(args.graph, results)
        graph_writer.write(args.graph)
        print(f"Graph saved to: {args.graph}")

if __name__ == "__main__":
    run_cli()
