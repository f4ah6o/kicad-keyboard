# KiCad Keyboard - Grin配列

KiCad用のGrin配列キーボードレイアウトプロジェクトです。

## 概要

このプロジェクトは、人間工学的なキーボードレイアウトである**Grin配列**を実装するためのツールとシミュレータを提供します。Grin配列は、水平区間と円弧区間を組み合わせた独自のキー配置パターンで、手の自然な動きに沿った配置を実現します。

### Grin配列の特徴

- **ハイブリッド配置**: 水平 → 下側円弧 → 上側円弧 → 下側円弧 → 水平
- **共通中心**: 複数行で共通の円弧中心を共有
- **人間工学的設計**: 下段ほど半径を小さくし、手の動きに追従
- **角接触配置**: キー間の接触を円中心側の角で制御

## プロジェクト構成

```
kicad-keyboard/
├── docs/                    # ドキュメント
│   └── plan.md             # Grin配列の設計仕様と実装計画
├── simulator/               # Pythonシミュレータ
│   ├── grin_simulator.py   # シミュレータ本体
│   ├── footprint.py        # フットプリントデータ構造
│   ├── api.py              # コアAPI関数
│   ├── visualizer.py       # 可視化ツール
│   ├── example.py          # 使用例
│   └── README.md           # シミュレータの詳細ドキュメント
└── LICENSE                  # MITライセンス
```

## 主要機能

### 1. Pythonシミュレータ

Grin配列のレイアウトをシミュレートし、可視化します。

- **最小API設計**: 3つのコア関数で実装
  - `place_on_arc()` - 円弧上への配置
  - `orient_to_tangent()` - 接線方向への回転
  - `snap_corner()` - 角のスナップ
- **間隙/干渉チェック**: `evaluate_spacing()` / `footprint_spacing()` でキー間クリアランスを解析
- **可視化機能**: Matplotlibによる配置結果の描画
- **柔軟なパラメータ**: 行数、列数、半径、ピッチなどをカスタマイズ可能
- **JSONスナップショット**: `simulator/exports/*.json` に初期/最終レイアウトを自動出力
- **KLE初期配置**: `simulator/layouts/standard_35_kle.json`（Keyboard Layout Editor形式）を読み込み、初期状態を一般的なスタッカード配列で可視化
- **PNGスナップショット**: 各サンプルで初期・最終それぞれの PNG を自動生成

詳細は [simulator/README.md](simulator/README.md) を参照してください。

### 2. 設計仕様

Grin配列の詳細な設計仕様とアルゴリズムは [docs/plan.md](docs/plan.md) に記載されています。

## クイックスタート

### 必要要件

- Python 3.10以上
- [uv](https://github.com/astral-sh/uv) 0.9 以降（推奨）
- KiCad (将来的な統合用)

### インストールと使用

1. **リポジトリのクローン**

```bash
git clone https://github.com/f4ah6o/kicad-keyboard.git
cd kicad-keyboard
```

2. **依存パッケージのインストールとサンプル実行 (uv推奨)**

uv は `pyproject.toml` / `uv.lock` に記述された依存関係を自動で解決します。

```bash
# ルートディレクトリで実行
uv sync                 # 初回のみ。 .venv が作成される
uv run python simulator/example.py
```

`uv sync` を省略しても `uv run` 時に自動で依存関係が解決されます。`grin_layout_*.png`（初期・最終）と `simulator/exports/*.json` が生成されれば成功です。初期状態は `simulator/layouts/standard_35_kle.json` による 35 キーのスタッカード配列になります。

3. **pip を使う場合の代替手順**

```bash
cd simulator
pip install -r requirements.txt
python example.py
```

### 基本的な使い方

```python
from grin_simulator import GrinSimulator
from visualizer import plot_grin_layout

# シミュレータの作成
sim = GrinSimulator(
    rows=3,                    # 行数
    cols=10,                   # 列数
    center=(150.0, 150.0),     # 円弧の中心座標
    base_radius=120.0,         # 最上段の半径
    radius_step=15.0,          # 行ごとの半径減少量
    base_pitch=19.05           # キーピッチ (mm)
)

# レイアウトの実行
sim.layout()

# 結果の可視化
plot_grin_layout(sim, filename="my_layout.png")
```

## 設計原則

このプロジェクトは以下の原則に基づいて設計されています：

1. **最小API**: 必要最小限の関数で実装し、理解しやすく保守しやすいコードを実現
2. **数値安定性**: `pitch/(2R) ≤ 1` を保証し、三角関数の定義域を確保
3. **角接触**: キー同士の配置は中心側の角で接触させる一貫した方式
4. **制約遵守**: 下側円弧は左右各2キーまで（最下段除く）
5. **スクリーン座標系**: Y軸の正方向を下向きにし、下段ほど Y が大きくなるよう統一

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## コントリビューション

バグ報告や機能提案は、GitHubのIssuesでお願いします。プルリクエストも歓迎します。

## 今後の計画

- [ ] KiCadプラグインの実装
- [ ] キーマップのカスタマイズ機能
- [ ] 3Dプレビュー機能
- [ ] より多様なキーボードレイアウトのサポート

## 関連リンク

- [KiCad](https://www.kicad.org/) - オープンソースの電子設計自動化ツール
- [人間工学的キーボード設計](https://en.wikipedia.org/wiki/Ergonomic_keyboard)

---

© 2025 f12o
