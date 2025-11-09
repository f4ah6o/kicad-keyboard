# Tests

このディレクトリには、kicad-keyboard プロジェクトの包括的なテストスイートが含まれています。

## テスト構成

- **test_footprint.py**: Footprint クラスの機能テスト
- **test_api.py**: コア API 関数のテスト
- **test_grin_simulator.py**: GrinSimulator クラスのテスト
- **test_kle_layout.py**: KLE レイアウトの解析と適用のテスト
- **test_visualizer.py**: 可視化機能のテスト

## テストの実行

```bash
# 依存関係のインストール
uv sync --all-extras

# テストの実行
uv run pytest

# 詳細出力付きでテスト実行
uv run pytest -v

# カバレッジレポート付きでテスト実行
uv run pytest -v --cov=simulator --cov-report=html
```

## テスト結果

現在のテストスイート:
- **56個のテスト**
- **カバレッジ: 74%**

## CI/CD

GitHub Actions ワークフローの設定は `.github/workflows/test.yml` に記載されています（ローカル作成済み）。

このファイルをリポジトリに追加するには、`workflows` 権限を持つアカウントで手動でコミットしてください：

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install uv
      uses: astral-sh/setup-uv@v4
      with:
        version: "latest"
    - name: Install dependencies
      run: uv sync --all-extras
    - name: Run tests with pytest
      run: uv run pytest -v --cov=simulator --cov-report=xml --cov-report=term
```

## テストの追加

新しいテストを追加する際は：

1. `tests/test_*.py` の形式でファイルを作成
2. `Test*` クラスでテストケースをグループ化
3. `test_*` 関数でテストケースを記述
4. `pytest` が自動的に検出して実行します
