# キャッシュフロー表システム 仕様書

## 1. システム概要
本システムは、将来のライフプラン検討のために、長期的なキャッシュフロー（収支・資産推移）をシミュレーション・管理するためのシステムです。
ユーザーが作成したYAML形式の設定ファイルを読み込み、年次ごとの収支と資産残高を計算し、CSV形式で出力します。
CLI（コマンドラインインターフェース）での実行を基本とし、データベースを介さないシンプルな構成で、複数のライフプラン・シナリオを迅速に試行することを目的とします。

## 2. 機能要件

### 2.1 ユーザー管理
- 夫婦2名（本人・配偶者）を基本構成とする。
- それぞれの生年月日、退職予定年齢、年金受給開始年齢などの基本属性を管理する。

### 2.2 収入管理
以下の項目を、本人・配偶者別に管理できること。
- **給与収入**: 月額、賞与、昇給率
- **パート収入**: 時給、労働時間、または月額
- **個人事業収入**: 売上、経費、利益
- **雑収入**: 講演料、原稿料、副業収入など
- **年金収入**: 
    - 公的年金（老齢基礎年金、老齢厚生年金）
    - 規約型企業年金
    - 個人年金

### 2.3 支出管理
世帯全体の支出として、以下の項目を管理できること。
- **住居費**:
    - 住宅ローン（返済額、ボーナス払い、残高、期間）
    - 固定資産税
    - 管理費・修繕積立金
- **基本生活費**:
    - 食費
    - 光熱費
    - 通信費、日用品、娯楽費等
- **その他支出**: 教育費、車両維持費、臨時支出など

### 2.4 資産・口座管理
以下の口座別の残高推移を管理できること。
- **生活費口座**: 日々の入出金を行うメイン口座。不足時は他の口座から補填される。
- **生活防衛資金口座**: 緊急時に備えた流動性の高い預金
- **NISA**: 新NISA（つみたて投資枠・成長投資枠）に対応した運用
- **DC/iDeCo**: 確定拠出年金、個人型確定拠出年金
- **総合口座**: その他投資・貯蓄用口座。
    - **証券ポジション**: 株式、投資信託などの運用資産。
    - **現金ポジション**: 国債、スイッチ預金などの低リスク・流動性資産。

### 2.5 計算機能
- **キャッシュフローシミュレーション**: 指定された年数（例：100歳まで）の毎年の収支と資産残高を計算する。
- **インフレ率対応**: 
    - 指定されたインフレ率（物価上昇率）に基づき、将来の支出額を補正計算する。
    - 運用利回りとインフレ率を考慮した実質価値の計算。
- **運用計算**: NISAやiDeCo等の口座における期待利回りに基づく資産成長計算。
- **資産取り崩し戦略**:
    - 生活費口座がマイナスになる場合、指定された優先順位に従い他の口座（総合口座、NISA等）から資金を移動し、生活資金がマイナスにならないようにする。
    - 特定の年齢や条件において、資産を「定額」または「定率」で取り崩し、生活費口座へ移動する戦略を指定できる。

## 3. データモデルと入力形式

### 3.1 YAMLによる入力定型
ユーザーは設定や初期データをYAML形式で記述します。システムはこのファイルを直接読み込んでシミュレーションを実行します。

```yaml
# example_input.yaml
simulation_settings:
  inflation_rate: 0.01
  duration_years: 50
  start_year: 2026

members:
  - name: "本人"
    role: "self"
    birth_date: "1980-01-01"
    retirement_age: 65
    pension_start_age: 65
  - name: "配偶者"
    role: "spouse"
    birth_date: "1982-05-15"
    retirement_age: 65
    pension_start_age: 65

income_entries:
  - member: "本人"
    category: "salary"
    amount: 5000000
    start_year: 2026
    end_year: 2045
    growth_rate: 0.01
  - member: "本人"
    category: "miscellaneous"
    amount: 500000
    start_year: 2026
    end_year: 2030
  - member: "本人"
    category: "pension"
    amount: 2200000
    start_year: 2045
    end_year: 2074
    growth_rate: 0.0
  - member: "本人"
    category: "pension_corporate"
    amount: 600000
    start_year: 2045
    end_year: 2054
    growth_rate: 0.0
  - member: "本人"
    category: "pension_corporate"
    amount: 300000
    start_year: 2045
    end_year: 2074
    growth_rate: 0.0
  - member: "配偶者"
    category: "pension"
    amount: 1200000
    start_year: 2047
    end_year: 2074
    growth_rate: 0.0
  - member: "配偶者"
    category: "pension_corporate"
    amount: 400000
    start_year: 2047
    end_year: 2056
    growth_rate: 0.0

expense_entries:
  - category: "food"
    amount: 600000
    start_year: 2026
    end_year: 2074
    inflation_indexed: true

accounts:
  - name: "living"
    initial_balance: 1000000
    expected_return: 0.0
  - name: "nisa"
    initial_balance: 2000000
    expected_return: 0.05
  - name: "dc"
    initial_balance: 1000000
    expected_return: 0.03
  - name: "general"
    initial_balance: 3000000
    expected_return: 0.04
    cash_ratio: 0.1
```

### 3.2 データ構造（入力パラメーター）
YAMLから読み込まれるデータ項目は以下の通りです。

#### Simulation Settings (シミュレーション全体設定)
- `inflation_rate`: インフレ率（物価上昇率）
- `duration_years`: シミュレーション実行期間（年）

#### Members (世帯員)
- `name`: 名前
- `role`: 役割 ('self' or 'spouse')
- `birth_date`: 生年月日
- `retirement_age`: 退職予定年齢
- `pension_start_age`: 公的年金受給開始年齢

#### Income Entries (収入項目)
- `member`: 該当する世帯員名
- `category`: カテゴリ ('salary', 'part_time', 'business', 'miscellaneous', 'pension_corporate', 'pension_private')
    - 同一人に対して同一カテゴリの項目（例：複数の企業年金）を複数定義することが可能です。
- `amount`: 年間金額
- `start_year`: 開始年
- `end_year`: 終了年
- `growth_rate`: 昇給率/増減率

#### Expense Entries (支出項目)
- `category`: カテゴリ ('mortgage', 'property_tax', 'management_fee', 'food', 'utility', 'others')
- `amount`: 年間金額
- `start_year`: 開始年
- `end_year`: 終了年
- `inflation_indexed`: インフレ率を適用するかどうか (boolean)

#### Accounts (口座情報)
- `name`: 口座名 ('living', 'defense', 'nisa', 'ideco', 'general')
- `initial_balance`: シミュレーション開始時の残高
- `expected_return`: 期待利回り (運用利回り)
- `cash_ratio`: （総合口座のみ）現金ポジションの割合 (0.0 - 1.0)
- `withdrawal_strategy`: 取り崩し戦略
    - `type`: 戦略タイプ ('fixed_amount': 定額, 'fixed_rate': 定率)
    - `amount`: 定額取り崩し時の金額
    - `rate`: 定率取り崩し時の割合
    - `start_age`: 取り崩し開始年齢

## 4. 計算ロジック

### 4.1 インフレ率の適用
将来の支出額 $E_n$ は、現在の支出額 $E_0$、インフレ率 $r$、経過年数 $n$ とすると以下で計算する。
$$E_n = E_0 \times (1 + r)^n$$
※住居費（固定ローン）など、インフレの影響を受けない項目は除外設定を可能とする。

### 4.2 資産残高の更新
各年の期末残高 $B_n$ は、期首残高 $B_{n-1}$、運用利回り $i$、年間収支 $CF_n$ とすると以下で計算する。
$$B_n = B_{n-1} \times (1 + i) + CF_n$$

### 4.3 資金補填ロジック
生活費口座の残高が 0 を下回る場合、以下の優先順位で他の口座から不足分を取り崩す。
1. 総合口座（現金ポジション）
2. 総合口座（証券ポジション）
3. NISA（成長投資枠）
4. NISA（つみたて投資枠）
※ iDeCo等、特定の年齢まで引き出し制限がある口座は、条件を満たすまで除外する。
すべての資産を合算しても不足する場合は、生活費口座の残高はマイナスのまま（債務状態）として記録する。

## 5. 出力
### 5.1 CSV出力
- シミュレーション結果（年次ごとの収支・資産残高）をCSV形式で出力する。
- 出力されたCSVは、LibreOffice（Calc）等の表計算ソフトで読み込み、ユーザーが任意にグラフ作成や詳細分析を行えるようにする。

## 6. 技術スタック（選定案）
本システムは、以下の技術スタックを用いて実装します。

### 6.1 実行プラットフォーム
- **Python 3.x**: 
    - 理由: ユーザーが使い慣れており、将来的なグラフ生成（matplotlib）や高度なデータ分析への拡張性が高いため。
    - CLIツールとしての実績、簡潔な文法。

### 6.2 主要ライブラリ
- **PyYAML**: YAML設定ファイルのパースに使用。
- **csv (標準ライブラリ)**: 計算結果のCSV出力に使用。
- **argparse (標準ライブラリ)**: CLI引数の処理に使用。
- **datetime (標準ライブラリ)**: 日付・年齢計算に使用。
- **matplotlib (将来拡張)**: 資産推移のグラフ化に使用。

## 7. ユーザーインタフェース（想定）
- **YAML入力データ**: ユーザーは `example_input.yaml` などのファイルに収入、支出、資産、シミュレーション期間などの詳細を記述。
- **CLI実行**: コマンドラインからYAMLファイルを読み込み、計算を実行。
- **計算結果の出力**: 
    - 実行結果をターミナルに要約表示。
    - 年次ごとの詳細な収支・資産推移をCSV形式で保存。
- **再実行**: YAMLファイルを編集して再実行することで、複数のシナリオ（例：インフレ率の違い、退職時期の変更）を容易にシミュレーション可能。
