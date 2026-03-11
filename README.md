# CFtable (Cash Flow Simulation Tool)

CFtableは、長期的なキャッシュフロー（収支・資産推移）をシミュレーションするためのツールです。
YAML形式の設定ファイルを読み込み、年次ごとの収支と資産残高を計算し、CSVまたはODS形式で出力します。

## 主な機能

- **将来収支の試算**: 給与、年金、生活費、住宅ローンなどの推移を計算。
- **インフレ・昇給対応**: 物価上昇率や昇給率を考慮したシミュレーションが可能。
- **資産運用シミュレーション**: NISA、iDeCo、特定口座などの運用利回りを考慮。
- **自動投資機能**: 生活費口座の余剰資金を、優先順位（NISA → 総合口座）に従って自動的に投資に回します。
- **NISA上限管理**: NISAの年間投資枠および生涯投資枠を考慮した積立が可能です。
- **DC/iDeCo拠出**: 年齢制限（例：60歳まで）を考慮した定額拠出のシミュレーションが可能です。
- **税金考慮**: 総合口座（特定口座）からの取り崩し時、利益に対して20%の課税を考慮した手取り額を計算します。
- **自動資金補填**: 生活費が不足した場合、あらかじめ設定した優先順位に従って運用資産から自動的に補填（取り崩し）を行うロジックを搭載。
- **柔軟な取り崩し戦略**: 特定の年齢から「定額」または「定率」で資産を生活費口座へ移す戦略を設定可能。

## セキュリティと個人情報に関する注意

本ツールでは、家族構成、生年月日、年収、資産額などの機密性の高い個人情報を扱います。
これらの情報が含まれるファイルを、GitHub などの公開リポジトリ（fork を含む）に不用意にコミットしないよう十分注意してください。

### 推奨されるワークフロー

1.  **テンプレートのコピー**: `example_input.template.yaml` をコピーして、自分用の設定ファイルを作成します。
2.  **ローカルファイル名の使用**: 個人用ファイルには `*.local.yaml` または `*.private.yaml` という名前を付けることを推奨します。これらはデフォルトで `.gitignore` の対象となっており、誤ってコミットされるのを防げます。
    ```bash
    cp example_input.template.yaml my_plan.local.yaml
    ```
3.  **出力ファイルの管理**: シミュレーション結果（CSV/ODS）には資産推移や年齢などの情報が含まれます。出力ファイルも `output.private.csv` や `output.private.ods` のように命名し、公開リポジトリへのコミットを避けてください。

### 実行例
```bash
# CSV形式で出力（デフォルト）
cftable my_plan.local.yaml -o output.private.csv

# ODS形式で出力（拡張子で自動判別）
cftable my_plan.local.yaml -o output.private.ods
```

---

## インストール方法

リポジトリをクローンまたはダウンロードした後、以下のコマンドでインストールできます。
（Python 3.14が必要です）

```bash
pip install .
```

※依存ライブラリとして `PyYAML`, `matplotlib`, `odfpy` がインストールされます。

## 実行方法

インストール後、以下のコマンドでシミュレーションを実行できます。

### パッケージコマンドとして実行
```bash
# CSV出力
cftable input.yaml -o output.csv

# ODS出力
cftable input.yaml -o output.ods
```

### Pythonモジュールとして実行
```bash
python3 -m cftable input.yaml -o output.ods
```

**引数の解説:**
- `input.yaml`: 入力設定ファイル（必須）
- `-o`, `--output`: 出力ファイルのパス（任意、デフォルトは `output.csv`）
  - 拡張子が `.ods` の場合は ODS (OpenDocument Spreadsheet) 形式で出力されます。
  - それ以外の場合は CSV 形式で出力されます。

---

## テストの実行方法

toxを使用して、ユニットテストとインテグレーションテストを実行できます。

```bash
# すべてのテストを実行
tox

# 特定の環境を指定して実行
tox -e py314
```

---

## 入力ファイル（YAML）の解説

入力ファイルは以下の5つのセクションで構成されます。

### 1. simulation_settings (全体設定)
シミュレーションの基本条件を設定します。
- `inflation_rate`: 年間のインフレ率（例: `0.01` は 1%）
- `duration_years`: シミュレーションを行う期間（年）
- `start_year`: シミュレーション開始年

### 2. members (世帯員)
シミュレーションの対象となる家族（通常は本人と配偶者）を設定します。
- `name`: 名前（収入項目との紐付けに使用）
- `role`: 役割 (`self` (本人) または `spouse` (配偶者))
- `birth_date`: 生年月日 (`YYYY-MM-DD` 形式)
- `retirement_age`: 退職予定年齢
- `pension_start_age`: 公的年金の受給開始年齢

### 3. income_entries (収入項目)
給与や年金などの収入を定義します。
- `member`: 該当する世帯員名
- `category`: カテゴリ名 (`salary`, `pension`, `business` など)
- `amount`: 年間の収入額（円）
- `start_year`: 収入が発生する開始年
- `end_year`: 収入が終了する年
- `year`: (ワンショット収入のみ) 発生する年。`start_year`, `end_year` の代わりに指定可能。
- `growth_rate`: 年間の昇給率（例: `0.01` は 1%）

### 4. expense_entries (支出項目)
生活費やローンなどの支出を定義します。
- `category`: カテゴリ名 (`food`, `mortgage`, `utility` など)
- `amount`: 年間の支出額（円）
- `start_year`: 支出が発生する開始年
- `end_year`: 支出が終了する年
- `year`: (ワンショット支出のみ) 発生する年。`start_year`, `end_year` の代わりに指定可能。
- `inflation_indexed`: インフレ率を適用するかどうか (`true` または `false`)
  - 住宅ローンなどは `false`、食費などは `true` を推奨します。

### 5. accounts (口座・資産)
保有する資産口座と運用設定を定義します。
- `name`: 口座名 (`living` (生活費), `nisa`, `dc` (iDeCo等), `general` (総合口座) など)
  - `living` 口座は必須です（日々の収支がここに入金・出金されます）。
- `initial_balance`: シミュレーション開始時の残高
- `expected_return`: 年間の期待利回り（例: `0.05` は 5%）
- `initial_cost_basis`: シミュレーション開始時点での投資元本（NISAの上限管理や総合口座の課税計算に使用）
- `annual_investment_limit`: (NISAのみ) 年間の投資上限額
- `lifetime_investment_limit`: (NISAのみ) 生涯の投資上限額
- `contribution_amount`: (DC/iDeCoのみ) 年間の拠出額
- `contribution_end_age`: (DC/iDeCoのみ) 拠出を終了する年齢
- `withdrawal_strategy`: 取り崩し戦略（任意）
  - `type`: `fixed_amount` (定額) または `fixed_rate` (定率)
  - `amount`: 定額取り崩し時の年間金額
  - `rate`: 定率取り崩し時の年間率
  - `start_age`: 本人の年齢がこの年齢に達したら取り崩しを開始

---

## 資金補填の優先順位

生活費口座 (`living`) がマイナスになった場合、システムは自動的に以下の優先順位で他の口座から資金を補填します。

1. **総合口座 (tokutei)**
2. **NISA** 口座（名前に「成長」または「growth」が含まれるものを優先）
3. **iDeCo / DC**（本人の年齢が60歳以上の場合のみ）

---

## 出力結果について

実行が完了すると、以下の情報が出力されます。

### ターミナル表示
- シミュレーション期間
- 初期資産額、最終資産額
- 最小資産額（最も資産が減る時期とその金額）

### CSV/ODSファイル
指定したファイル名（デフォルト `output.csv`）で保存されます。拡張子が `.ods` の場合は ODS 形式、それ以外は CSV 形式となります。
- 年次ごとの収入、支出、キャッシュフロー
- 各口座別の期末残高
- 全資産合計
- 各世帯員の年齢

ODS形式で出力した場合、金額（円）は通貨型(JPY)、年や年齢は数値型として保存されるため、表計算ソフトでの再利用が容易です。

## ライセンス

このプロジェクトは [MIT ライセンス](LICENSE) の下で公開されています。
