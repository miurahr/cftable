# キャッシュフロー表システム 仕様書

## 1. システム概要
本システムは、将来のライフプラン検討のために、長期的なキャッシュフロー（収支・資産推移）をシミュレーション・管理するためのシステムです。
ユーザーが作成したYAML形式の設定ファイルを読み込み、年次ごとの収支と資産残高を計算し、CSVまたはODS形式で出力します。
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
- **その他支出**: 教育費（子供の年齢に基づいた計算が可能）、車両維持費、臨時支出など

### 2.4 資産・口座管理
以下の口座別の残高推移を管理できること。
- **生活費口座**: 日々の入出金を行うメイン口座。不足時は他の口座から補填される。
- **生活防衛資金口座**: 緊急時に備えた流動性の高い預金
- **NISA**: 新NISA（つみたて投資枠・成長投資枠）に対応した運用
- **DC/iDeCo**: 確定拠出年金、個人型確定拠出年金
- **特定口座**: その他投資・貯蓄用口座。
    - **証券ポジション**: 株式、投資信託などの運用資産。
    - **現金ポジション**: 国債、スイッチ預金などの低リスク・流動性資産。

### 2.5 計算機能
- **キャッシュフローシミュレーション**: 指定された年数（例：100歳まで）の毎年の収支と資産残高を計算する。
    - **計算順序**: 
        1. 収入・支出の計算（基礎収支の確定）
        2. 口座からの取り崩し（予定された取り崩し、および生活費不足分の補填）
        3. 運用利回りの適用（取り崩し後の残高に対して利回りを計算）
        4. 余剰資金の投資（NISA、特定口座等への再投資）
- **インフレ率対応**: 
    - 指定されたインフレ率（物価上昇率）に基づき、将来の支出額を補正計算する。
    - 運用利回りとインフレ率を考慮した実質価値の計算。
- **運用計算**: NISAやiDeCo等の口座における期待利回りに基づく資産成長計算。
- **資産取り崩し戦略**:
    - 生活費口座がマイナスになる場合、指定された優先順位に従い他の口座（特定口座、NISA等）から資金を移動し、生活資金がマイナスにならないようにする。
    - 特定の年齢や条件において、資産を「定額」または「定率」で取り崩し、生活費口座へ移動する戦略を指定できる。
    - **投資制限**: 取り崩し戦略が開始された口座については、以降の余剰資金の自動投入（再投資）は行われず、余剰分は生活費口座に維持される。

## 3. データモデルと入力形式

### 3.1 YAMLによる入力定型
ユーザーは設定や初期データをYAML形式で記述します。システムはこのファイルを直接読み込んでシミュレーションを実行します。

```yaml
# example_input.template.yaml
simulation_settings:
  inflation_rate: 0.01
  end_age: 90
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

  - category: "education"   # 教育費 (子供の進学に合わせて設定)
    member: "第一子"         # 該当する家族の名前を指定
    amount: 1000000         # 小学校入学(6歳)から中学卒業(15歳)まで年 100 万
    start_age: 6
    end_age: 15
    inflation_indexed: true

  - category: "housing_maintenance" # 住宅設備（給湯器・エアコン等）の買い替え
    amount: 500000                # 買い替え費用（目安）
    start_year: 2035              # 次回の買い替え予定年
    end_year: 2074                # シミュレーション終了まで
    repeat_interval: 15           # 15年おきに発生
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
  - name: "tokutei"
    initial_balance: 3000000
    expected_return: 0.04
    cash_ratio: 0.1
```

### 3.2 データ構造（入力パラメーター）
YAMLから読み込まれるデータ項目は以下の通りです。

#### Simulation Settings (シミュレーション全体設定)
- `inflation_rate`: インフレ率（物価上昇率）
- `duration_years`: シミュレーション実行期間（年）。`end_age` との選択。
- `end_age`: 主メンバー (`role: self`) がこの年齢になるまで計算する。`duration_years` が指定されていない場合に使用される。
- `start_year`: シミュレーション開始年

#### Members (世帯員)
- `name`: 名前
- `role`: 役割 ('self' or 'spouse')
- `birth_date`: 生年月日
- `retirement_age`: 退職予定年齢
- `pension_start_age`: 公的年金受給開始年齢

#### Income Entries (収入項目)
- `member`: 該当する世帯員名
- `category`: カテゴリ ('salary', 'part_time', 'business', 'miscellaneous', 'pension', 'pension_corporate', 'pension_private', 'retirement' など)
    - 同一人に対して同一カテゴリの項目（例：複数の企業年金）を複数定義することが可能です。
- `amount`: 年間金額
- `start_year` / `end_year`: 開始年・終了年
- `year`: (ワンショット収入のみ) 発生する年。`start_year`, `end_year` の代わりに指定可能。
- `start_age` / `end_age`: 開始年齢・終了年齢 (`member` で指定した世帯員の年齢に基づく計算)
- `growth_rate`: 昇給率/増減率
- `repeat_interval`: 繰り返し間隔（年）。指定した場合、`start_year`（または `start_age`）からこの年数おきに発生する。

#### Expense Entries (支出項目)
- `category`: カテゴリ ('mortgage', 'property_tax', 'management_fee', 'food', 'utility', 'medical', 'tax_and_insurance', 'education', 'housing_maintenance' など)
- `amount`: 年間金額
- `start_year` / `end_year`: 開始年・終了年
- `year`: (ワンショット支出のみ) 発生する年。`start_year`, `end_year` の代わりに指定可能。
- `start_age` / `end_age`: 開始年齢・終了年齢 (`member` で指定した世帯員の年齢に基づく計算)
- `member`: 年齢計算の基準とする世帯員名 (省略時は 'role: self' のメンバー)
- `inflation_indexed`: インフレ率を適用するかどうか (boolean)
- `growth_rate`: 増減率 (インフレとは別に適用される)
- `repeat_interval`: 繰り返し間隔（年）。指定した場合、`start_year`（または `start_age`）からこの年数おきに発生する。

#### Accounts (口座情報)
- `name`: 口座名 ('living', 'nisa', 'ideco', 'tokutei')
- `initial_balance`: シミュレーション開始時の残高
- `expected_return`: 期待利回り (運用利回り)
- `cash_ratio`: （特定口座のみ）現金ポジションの割合 (0.0 - 1.0)
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
各年の期末残高 $B_n$ は、期首残高 $B_{n-1}$、運用利回り $i$、年間収支 $CF_n$、および取り崩し額 $W_n$ とすると、以下のような順序で計算される。
1. 基礎収支適用: $B'_{n} = B_{n-1} + CF_n$ （生活費口座への反映）
2. 取り崩し実行: $B''_{n} = B'_{n} - W_n$ （投資口座からの取り出し）
3. 運用利回り適用: $B_{n} = B''_{n} \times (1 + i)$ （残高に対する利回り適用）
4. 余剰投資: 利回り適用後の残高に対し、生活費口座の余剰分を再投資。

### 4.3 資金補填ロジック
生活費口座の残高が 0 を下回る場合、以下の優先順位で他の口座から不足分を取り崩す。
1. 特定口座（現金ポジション）
2. 特定口座（証券ポジション）
3. NISA（成長投資枠）
4. NISA（つみたて投資枠）
※ iDeCo等、特定の年齢まで引き出し制限がある口座は、条件を満たすまで除外する。
すべての資産を合算しても不足する場合は、生活費口座の残高はマイナスのまま（債務状態）として記録する。

## 5. 出力
### 5.1 CSV/ODS出力
- シミュレーション結果（年次ごとの収支・資産残高）をCSVまたはODS形式で出力する。
- 出力ファイルの拡張子が `.ods` の場合は ODS (OpenDocument Spreadsheet) 形式、それ以外は CSV 形式で出力される。
- 主な出力項目:
    - `year`: 年
    - `income`: 外部からの収入合計（給与、年金等。口座からの取り崩しは含まない）
    - `withdrawal`: 口座からの取り崩し額合計
    - `expense`: 支出合計
    - `cash_flow`: 年間収支（income - expense）
    - `living_balance`: 生活費口座残高
    - `total_assets`: 総資産額
- 出力されたCSV/ODSは、LibreOffice（Calc）やExcel等の表計算ソフトで読み込み、ユーザーが任意にグラフ作成や詳細分析を行えるようにする。
- ODS形式では、金額列は通貨型(JPY)、年・年齢列は数値型として出力される。

## 6. 技術スタック（選定案）
本システムは、以下の技術スタックを用いて実装します。

### 6.1 実行プラットフォーム
- **Python 3.x**: 
    - 理由: ユーザーが使い慣れており、将来的なグラフ生成（matplotlib）や高度なデータ分析への拡張性が高いため。
    - CLIツールとしての実績、簡潔な文法。

### 6.2 主要ライブラリ
- **PyYAML**: YAML設定ファイルのパースに使用。
- **csv (標準ライブラリ)**: 計算結果のCSV出力に使用。
- **odfpy**: 計算結果のODS出力に使用。
- **argparse (標準ライブラリ)**: CLI引数の処理に使用。
- **datetime (標準ライブラリ)**: 日付・年齢計算に使用。
- **matplotlib (将来拡張)**: 資産推移のグラフ化に使用。

## 7. ユーザーインタフェース（想定）
- **YAML入力データ**: ユーザーは `example_input.template.yaml` などのファイルに収入、支出、資産、シミュレーション期間などの詳細を記述。
- **CLI実行**: コマンドラインからYAMLファイルを読み込み、計算を実行。
- **計算結果の出力**: 
    - 実行結果をターミナルに要約表示。
    - 年次ごとの詳細な収支・資産推移をCSVまたはODS形式で保存。
- **再実行**: YAMLファイルを編集して再実行することで、複数のシナリオ（例：インフレ率の違い、退職時期の変更）を容易にシミュレーション可能。
