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

#### 1. シンプルなレイアウト作成と可視化

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

#### 2. KLE形式レイアウトの読込と適用

標準的なキーボードレイアウトエディタ（[Keyboard Layout Editor](http://keyboard-layout-editor.com)）のJSON形式を読み込み、初期状態のキー数をシミュレータに適用できます：

```python
from grin_simulator import GrinSimulator
from kle_layout import load_kle_layout, apply_kle_layout
from visualizer import plot_grin_layout

# KLE形式のレイアウト読込
kle = load_kle_layout("simulator/layouts/standard_35_kle.json")

# シミュレータ作成と初期化
sim = GrinSimulator(
    rows=3,
    cols=10,
    center=(150.0, 150.0),
    base_radius=120.0,
    radius_step=15.0,
    base_pitch=19.05
)

# KLEレイアウトを適用（キー数を同期）
apply_kle_layout(sim, kle)

# レイアウト実行
sim.layout()

# 初期配置と最終配置の可視化
plot_grin_layout(sim, filename="initial.png", show_final=False)
plot_grin_layout(sim, filename="final.png", show_final=True)
```

#### 3. 間隙解析と品質評価

キー間のクリアランスと干渉を詳細に解析：

```python
from grin_simulator import GrinSimulator
from api import evaluate_spacing

sim = GrinSimulator(rows=3, cols=10, center=(150.0, 150.0),
                   base_radius=120.0, radius_step=15.0)
sim.layout()

# 間隙・干渉の解析
spacing_results = evaluate_spacing(sim)

# 結果の確認
for row_idx, row_spacing in enumerate(spacing_results):
    print(f"Row {row_idx}: {row_spacing}")
```

## 出力形式と結果の解釈

### 生成ファイル

#### PNG画像ファイル
`example.py` 実行時に以下のPNGファイルが自動生成されます：

- `grin_layout_basic.png` - シンプル設定での初期・最終配置
- `grin_layout_custom.png` - カスタムパラメータでの初期・最終配置
- `grin_layout_compact.png` - コンパクト設定での初期・最終配置
- `grin_layout_api_demo.png` - API デモンストレーション結果

各ファイルには2つのサブプロット：
- **左側（初期配置）**: KLE形式で指定された標準配置（スタッカード）
- **右側（最終配置）**: Grin配列に最適化されたレイアウト

#### JSONスナップショット
`simulator/exports/` ディレクトリに出力される `.json` ファイル：

```json
{
  "config": {
    "rows": 3,
    "cols": 10,
    "center": [150.0, 150.0],
    "base_radius": 120.0,
    "radius_step": 15.0,
    "base_pitch": 19.05
  },
  "footprints": [
    {
      "key_id": "0_0",
      "center": [150.0, 100.0],
      "corners": {
        "NE": [159.525, 90.475],
        "NW": [140.475, 90.475],
        "SE": [159.525, 109.525],
        "SW": [140.475, 109.525]
      }
    },
    ...
  ],
  "spacing": {
    "min_distance": 0.45,
    "max_distance": 18.32,
    "has_interference": false
  }
}
```

### 結果の解釈

#### 間隙評価
- `spacing` オブジェクトの `min_distance` がキー間の最小クリアランス
- `has_interference` が `true` の場合、キー間に干渉が発生している
- 快適な配置の目安：最小クリアランス > 0.5mm

#### コーナー座標
各キーフットプリントの4つのコーナー座標（NE/NW/SE/SW）により、正確なキー境界を確認可能。カスタムPCB設計時に参照できます。

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

### 優先度の高い機能

- [ ] **KiCadプラグイン化** - Python スクリプトを KiCad の PCBnew プラグインとして実装
  - KiCad上でGrin配列レイアウトを直接作成・編集
  - シミュレーション結果をPCB設計に自動反映

- [ ] **キーマップカスタマイズUI** - インタラクティブなGUI
  - キー配置を視覚的にドラッグ&ドロップで調整
  - パラメータのリアルタイムプレビュー

### 拡張機能

- [ ] **3Dプレビュー** - キーキャップの3Dモデル表示
  - OpenGLベースの可視化
  - キーボード立体構造の確認

- [ ] **多様なレイアウト対応**
  - ソリッドキーボード型
  - スプリットキーボード型
  - エルゴノミック湾曲型

- [ ] **PCB自動生成** - KiCad PCBファイル（`.kicad_pcb`）の直接生成
  - フットプリント配置の自動化
  - パッド配線の最適化提案

## 関連リンク

- [KiCad](https://www.kicad.org/) - オープンソースの電子設計自動化ツール
- [人間工学的キーボード設計](https://en.wikipedia.org/wiki/Ergonomic_keyboard)

---

© 2025 f12o
