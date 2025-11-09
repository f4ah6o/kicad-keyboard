# Grin Array Keyboard Simulator

Pythonで実装された、Grin配列キーボードレイアウトのシミュレータです。

## 概要

このシミュレータは、`docs/plan.md` に記載された仕様に基づいて、キーボードのキーフットプリントを **Grin配列**（水平 → 下側円弧 → 上側円弧 → 下側円弧 → 水平）に配置します。

### 主要機能

- **最小API設計**: 3つのコア関数 + 2つのユーティリティ関数
- **円弧配置**: 複数行で共通中心を共有し、下段ほど半径を小さくする
- **角接触**: 円中心側の角どうしを基準とした配置
- **可視化**: Matplotlibによる配置結果の可視化
- **JSONスナップショット**: `example.py` 実行時に初期/最終レイアウトを `exports/*.json` に保存
- **干渉評価API**: `footprint_spacing()` / `evaluate_spacing()` で干渉や間隙を数値化
- **PNGスナップショット**: 各サンプルで初期・最終の PNG を自動生成

## インストール

### uv を使う場合（推奨）

（リポジトリのルートで実行します）

```bash
uv sync
uv run python simulator/example.py
```

`uv run` だけでも依存関係が自動解決され、`grin_layout_*.png` と `exports/*.json` が生成されます。

### pip を使う場合

```bash
pip install -r requirements.txt
python example.py
```

## 使い方

### 基本的な使用例

```python
from grin_simulator import GrinSimulator
from kle_layout import load_kle_layout, apply_kle_layout
from visualizer import plot_grin_layout

# シミュレータを作成
sim = GrinSimulator(
    rows=4,                    # 行数
    cols=11,                   # 最大列数
    center=(150.0, 150.0),     # 円弧の中心座標
    base_radius=120.0,         # 最上段の半径
    radius_step=15.0,          # 行ごとの半径減少量
    base_pitch=19.05,          # キーピッチ (mm)
    cols_per_row=[11, 10, 10, 4]  # 行ごとのキー数
)

# 初期配置を KLE データから読み込み
layout = load_kle_layout("layouts/standard_35_kle.json")
apply_kle_layout(sim, layout)

# レイアウトを実行
sim.layout()

# 結果を可視化
plot_grin_layout(sim, filename="output.png")
```

### サンプルの実行

複数のサンプル例を実行:

```bash
cd simulator
python example.py
```

これにより以下のファイルが生成されます:
- `grin_layout_basic.png` - 基本的なレイアウト
- `grin_layout_basic_initial.png` - 基本例の初期配置
- `grin_layout_custom.png` - カスタムパラメータのレイアウト
- `grin_layout_custom_initial.png` - カスタム例の初期配置
- `grin_layout_compact.png` - コンパクトなレイアウト
- `grin_layout_compact_initial.png` - コンパクト例の初期配置
- `grin_layout_api_demo.png` - APIの直接使用例
- `exports/*.json` - 各例の初期/最終レイアウトと干渉解析結果
- `layouts/standard_35_kle.json` - KLE 形式のリファレンスレイアウト

## API リファレンス

### コア関数

#### `place_on_arc(fp, C, R, theta)`
フットプリントを円弧上に配置します。

- `fp`: Footprintオブジェクト
- `C`: 円弧の中心座標 (Cx, Cy)
- `R`: 半径
- `theta`: 角度 (ラジアン)
- `y_up` (任意引数): True で上向き正 / False で下向き正（既定）

#### `orient_to_tangent(fp, theta, orientation, y_up=False)`
フットプリントを接線方向に回転します。

- `fp`: Footprintオブジェクト
- `theta`: 角度 (ラジアン)
- `orientation`: "UPPER" または "LOWER"
- `y_up`: Y軸の向き (デフォルト: False、画面座標系)

#### `snap_corner(fp, which, target)`
フットプリントの角を目標位置にスナップします。

- `fp`: Footprintオブジェクト
- `which`: 角の指定 ('NE', 'NW', 'SE', 'SW')
- `target`: 目標座標 (x, y) または (他のFootprint, 角名)

### ユーティリティ関数

#### `angle_step(pitch, R)`
円弧上のキー間の角度刻みを計算します。

#### `circle_point(C, R, theta)`
円周上の点の座標を計算します。

- `y_up` (任意引数): True で上向き正 / False で下向き正（既定）

### 間隙 / 干渉評価

#### `footprint_spacing(fp_a, fp_b)`
2つのフットプリント間の距離 (gap) と干渉量 (penetration) を返します。

- `status`: `CLEARANCE`, `CONTACT`, `INTERFERENCE`
- `gap`: 0 以上の距離 (mm)
- `penetration`: 干渉時の最小分離量 (mm)

#### `evaluate_spacing(footprints, gap_threshold=0.5)`
複数のフットプリントを一括解析し、最小間隙や干渉ペア、閾値以下の小さな隙間をレポートします。

## データ構造

### Footprint
キーフットプリントを表すクラス:

- `row`, `col`: 行・列インデックス
- `x`, `y`: 位置座標
- `rotation`: 回転角 (ラジアン)
- `width`, `height`: キーサイズ (mm)

### Section
レイアウトの区間を表すクラス:

- `type`: 区間タイプ (HORIZONTAL, UPPER_ARC, LOWER_ARC)
- `cols`: この区間に含まれる列のリスト
- `theta0`: 円弧区間の開始角度

## 設計原則

このシミュレータは `docs/plan.md` の仕様に従って実装されています:

1. **最小API**: 必要最小限の関数で実装
2. **角接触**: キー同士は中心側の角で接触
3. **制約遵守**: 下側円弧は左右各2キーまで（最下段除く）
4. **数値安定性**: `pitch/(2R) ≤ 1` を保証
5. **スクリーン座標系**: Y軸の正方向を下向きに統一

## ファイル構成

```
simulator/
├── __init__.py           # パッケージ初期化
├── footprint.py          # Footprintデータ構造
├── api.py                # コアAPI関数
├── grin_simulator.py     # シミュレータ本体
├── visualizer.py         # 可視化ツール
├── kle_layout.py         # KLE レイアウト読込ユーティリティ
├── example.py            # 使用例
├── layouts/              # Keyboard Layout Editor 形式のデータ
├── requirements.txt      # 依存パッケージ
└── README.md            # このファイル
```

## ライセンス

このプロジェクトの一部として提供されます。
