import unittest
from datetime import datetime
from cftable.models import Member, IncomeEntry, ExpenseEntry
from cftable.account import Account
from cftable.simulator import Simulator

class TestSimulator(unittest.TestCase):
    def setUp(self):
        self.settings = {
            'inflation_rate': 0.0,
            'duration_years': 5,
            'start_year': 2026
        }
        self.members = [
            Member(name="本人", role="self", birth_date=datetime(1980, 1, 1), retirement_age=65, pension_start_age=65)
        ]

    def test_initial_balance_preservation(self):
        """生活費口座の初期残高が維持されることを確認"""
        # 初期残高 100万円、収入なし、支出 50万円
        # 生活費口座から 50万円減るが、他の口座（defense）から補填されるはず
        accounts = [
            Account(name="living", initial_balance=1000000, expected_return=0.0),
            Account(name="defense", initial_balance=3000000, expected_return=0.0)
        ]
        income = []
        expense = [
            ExpenseEntry(category="living", amount=500000, start_year=2026, end_year=2030, inflation_indexed=False)
        ]
        
        sim = Simulator(self.settings, self.members, income, expense, accounts)
        sim.run()
        
        # 各年で living_balance が 100万円を維持しているか
        for res in sim.results:
            self.assertEqual(res['living_balance'], 1000000)
            # その分 defense が減っているはず
            year_idx = res['year'] - 2026
            expected_defense = 3000000 - 500000 * (year_idx + 1)
            self.assertEqual(res['defense_balance'], expected_defense)

    def test_defense_auto_allocation(self):
        """生活防衛資金が自動で確保されることを確認（支出の6ヶ月分）"""
        # 初期残高: living 100万, defense 0
        # 収入 500万, 支出 100万 -> 余剰 400万
        # defense の目標は 100万 * 0.5 = 50万
        accounts = [
            Account(name="living", initial_balance=1000000, expected_return=0.0),
            Account(name="defense", initial_balance=0, expected_return=0.0)
        ]
        income = [
            IncomeEntry(member="本人", category="salary", amount=5000000, start_year=2026, end_year=2030)
        ]
        expense = [
            ExpenseEntry(category="living", amount=1000000, start_year=2026, end_year=2030, inflation_indexed=False)
        ]
        
        sim = Simulator(self.settings, self.members, income, expense, accounts)
        sim.run()
        
        # 1年目で defense が 50万円確保されているはず
        self.assertEqual(sim.results[0]['defense_balance'], 500000)

    def test_nisa_limits(self):
        """NISAの年間投資枠と生涯投資枠が守られることを確認"""
        # NISA: 初期 0, 年間上限 120万, 生涯上限 200万
        # 収入 1000万, 支出 0 -> 余剰たっぷり
        accounts = [
            Account(name="living", initial_balance=0, expected_return=0.0),
            Account(name="nisa", initial_balance=0, expected_return=0.0, 
                    annual_investment_limit=1200000, lifetime_investment_limit=2000000)
        ]
        income = [
            IncomeEntry(member="本人", category="salary", amount=10000000, start_year=2026, end_year=2030)
        ]
        expense = []
        
        sim = Simulator(self.settings, self.members, income, expense, accounts)
        sim.run()
        
        # 1年目: 年間上限の120万まで
        self.assertEqual(sim.results[0]['nisa_balance'], 1200000)
        # 2年目: 残り 80万で生涯上限の200万に達する
        self.assertEqual(sim.results[1]['nisa_balance'], 2000000)
        # 3年目以降: 増えない
        self.assertEqual(sim.results[2]['nisa_balance'], 2000000)

    def test_dc_age_limit(self):
        """DC拠出が年齢制限で停止することを確認"""
        # 本人: 1980年生まれ。2040年に60歳。
        # 拠出終了年齢 60歳
        self.members[0].birth_date = datetime(1980, 1, 1)
        accounts = [
            Account(name="living", initial_balance=0, expected_return=0.0),
            Account(name="dc", initial_balance=0, expected_return=0.0,
                    contribution_amount=300000, contribution_end_age=60)
        ]
        income = [
            IncomeEntry(member="本人", category="salary", amount=5000000, start_year=2026, end_year=2050)
        ]
        expense = []
        settings = self.settings.copy()
        settings['duration_years'] = 20 # 2026 to 2045
        
        sim = Simulator(settings, self.members, income, expense, accounts)
        sim.run()
        
        # 2039年 (59歳) までは増える, 2040年 (60歳) は増えない
        # 2026 (46歳), ..., 2039 (59歳) -> 14年間
        res_2039 = next(r for r in sim.results if r['year'] == 2039)
        res_2040 = next(r for r in sim.results if r['year'] == 2040)
        
        self.assertEqual(res_2039['dc_balance'], 300000 * 14)
        self.assertEqual(res_2040['dc_balance'], 300000 * 14)

    def test_tokutei_account_tax(self):
        """特定口座の取り崩し時に20%課税されることを確認"""
        # 初期 1000万, 元本 500万 -> 利益 500万
        # 100万取り崩そうとすると、利益率は 50%
        # 100万の内、利益は 50万。税金は 50万 * 0.2 = 10万。手取り 90万。
        # 不足分が 90万の場合、100万取り崩されるはず。
        accounts = [
            Account(name="living", initial_balance=1000000, expected_return=0.0),
            Account(name="tokutei", initial_balance=10000000, initial_cost_basis=5000000, expected_return=0.0)
        ]
        # 2026年に 90万円不足させる
        income = [
            IncomeEntry(member="本人", category="salary", amount=100000, start_year=2026, end_year=2026)
        ]
        expense = [
            ExpenseEntry(category="living", amount=1000000, start_year=2026, end_year=2026, inflation_indexed=False)
        ]
        # living は 100万(初期) + 10万(収入) - 100万(支出) = 10万。不足 90万。
        
        sim = Simulator(self.settings, self.members, income, expense, accounts)
        sim.run()
        
        # 1年目の結果
        res = sim.results[0]
        # 手取り 90万を得るために、100万取り崩されたはず
        # balance: 1000万 -> 900万
        self.assertEqual(res['tokutei_balance'], 9000000)
        self.assertEqual(res['living_balance'], 1000000)

    def test_oneshot_entry(self):
        """yearパラメータによる単発収支を確認"""
        accounts = [Account(name="living", initial_balance=0, expected_return=0.0)]
        income = [
            IncomeEntry.from_dict({'member': "本人", 'category': "bonus", 'amount': 1000000, 'year': 2027})
        ]
        expense = [
            ExpenseEntry.from_dict({'category': "car", 'amount': 500000, 'year': 2028})
        ]
        
        sim = Simulator(self.settings, self.members, income, expense, accounts)
        sim.run()
        
        res_2026 = next(r for r in sim.results if r['year'] == 2026)
        res_2027 = next(r for r in sim.results if r['year'] == 2027)
        res_2028 = next(r for r in sim.results if r['year'] == 2028)
        
        self.assertEqual(res_2026['income'], 0)
        self.assertEqual(res_2027['income'], 1000000)
        self.assertEqual(res_2028['expense'], 500000)

    def test_inflation_indexing(self):
        """インフレ率が支出に正しく適用されることを確認"""
        settings = self.settings.copy()
        settings['inflation_rate'] = 0.1 # 10% inflation
        
        accounts = [Account(name="living", initial_balance=0, expected_return=0.0)]
        expense = [
            ExpenseEntry(category="food", amount=1000, start_year=2026, end_year=2028, inflation_indexed=True),
            ExpenseEntry(category="rent", amount=1000, start_year=2026, end_year=2028, inflation_indexed=False)
        ]
        
        sim = Simulator(settings, self.members, [], expense, accounts)
        sim.run()
        
        res_2026 = sim.results[0]
        res_2027 = sim.results[1]
        
        # 2026年 (開始年): 両方 1000
        # 2027年 (1年後): food は 1000 * 1.1 = 1100, rent は 1000
        self.assertEqual(res_2026['expense'], 2000)
        self.assertEqual(res_2027['expense'], 2100)

    def test_withdrawal_strategy_age_resolve(self):
        """取り崩し戦略の年齢指定（start_age）が正しく年に変換されることを確認"""
        # 本人: 1980年生まれ。60歳は2040年。
        self.members[0].birth_date = datetime(1980, 1, 1)
        accounts = [
            Account(name="living", initial_balance=0, expected_return=0.0),
            Account(name="dc", initial_balance=10000000, expected_return=0.0,
                    withdrawal_strategy={'type': 'fixed_amount', 'amount': 1000000, 'start_age': 60})
        ]
        settings = self.settings.copy()
        settings['start_year'] = 2038
        settings['duration_years'] = 5 # 2038 to 2042
        
        sim = Simulator(settings, self.members, [], [], accounts)
        sim.run()
        
        # 2038 (58歳), 2039 (59歳) は 0
        # 2040 (60歳), 2041 (61歳), 2042 (62歳) は 100万
        res_2039 = next(r for r in sim.results if r['year'] == 2039)
        res_2040 = next(r for r in sim.results if r['year'] == 2040)
        
        self.assertEqual(res_2039['dc_withdrawal'], 0)
        self.assertEqual(res_2040['dc_withdrawal'], 1000000)

    def test_pension_aggregation_by_member(self):
        """複数のメンバーの年金が個別に集計されることを確認"""
        members = [
            Member(name="本人", role="self", birth_date=datetime(1970, 1, 1), retirement_age=65, pension_start_age=65),
            Member(name="配偶者", role="spouse", birth_date=datetime(1973, 1, 1), retirement_age=65, pension_start_age=65)
        ]
        accounts = [Account(name="living", initial_balance=0, expected_return=0.0)]
        income = [
            IncomeEntry(member="本人", category="pension", amount=2400000, start_year=2035, end_year=2040),
            IncomeEntry(member="配偶者", category="pension", amount=950000, start_year=2037, end_year=2040)
        ]
        expense = []
        settings = self.settings.copy()
        settings['start_year'] = 2035
        settings['duration_years'] = 5
        
        sim = Simulator(settings, members, income, expense, accounts)
        sim.run()
        
        # 2035: 本人分のみ
        res_2035 = next(r for r in sim.results if r['year'] == 2035)
        self.assertEqual(res_2035['income_本人_pension'], 2400000)
        self.assertEqual(res_2035.get('income_配偶者_pension', 0), 0)
        
        # 2037: 両方
        res_2037 = next(r for r in sim.results if r['year'] == 2037)
        self.assertEqual(res_2037['income_本人_pension'], 2400000)
        self.assertEqual(res_2037['income_配偶者_pension'], 950000)
        self.assertEqual(res_2037['income'], 2400000 + 950000)

if __name__ == '__main__':
    unittest.main()
