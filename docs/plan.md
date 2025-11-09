## 前提
* 目的：最小APIでフットプリントを **Grin配列**（水平 → 下側円弧 → 上側円弧 → 下側円弧 → 水平）へ再配置する。
* 座標系：列方向=x、行方向=y。複数行で **共通中心 C=(Cx,Cy)** を共有し、下段ほど半径 R[r] を小さくする。
* 制約：**下側円弧は各行 左右2キーまで**（最下段除外）、**円弧切替は上側優先**、**角接触**（円中心側の角どうし）を基準とする。
* 最小API（3+2ユーティリティ）の方針：  
  * `place_on_arc(fp, C, R, theta)` … 円弧上の中心座標に配置  
  * `orient_to_tangent(fp, theta, orientation, y_up=True)` … 接線方向に回転  
  * `snap_corner(fp, which, target)` … 角を点または他フットプリント角にスナップ  
  * `angle_step = 2*asin(pitch/(2R))`（ユーティリティ）  
  * `circle_point(C,R,theta)`（ユーティリティ）

---

## ワークフロー（最小プロセス）

1. **基準設定**
   * 共通中心 `C` を決定し、各行に半径 `R[r]` とピッチ `P[r]` を割当。
   * 各行の角度刻みを算出：`Δθ[r] = 2*asin(P[r]/(2*R[r]))`。

2. **区間分割**
   * 各行の列範囲を **左水平 / 下側円弧 / 上側円弧 / 下側円弧 / 右水平** に分割。
   * 下側円弧は左右各2キー以内（最下段は除く）。切替は上側優先。

3. **水平区間配置（そのまま or 等ピッチ再整列）**
   * 回転は基準角（0°等）を維持。
   * 必要なら隣接の中心側角どうしを `snap_corner()` で整列。

4. **円弧区間配置（最小APIの定型シーケンス）**
   * 区間先頭キーの角度 `θ0` を決定（連続性を優先して前区間から決める）。
   * 以降、キー `n` は `θ = θ0 + n*Δθ[r]`。
   * 各キーで以下を順に実行：  
     * `place_on_arc(fp, C, R[r], θ)`  
     * `orient_to_tangent(fp, θ, orientation)`  *（orientation = "UPPER"|"LOWER"）*  
     * **角接触**：前キーの中心側角へ `snap_corner(fp, 'center_side', target=(prev,'center_side'))`
   * 横長キーは **短辺側の角** を「中心側角」として扱う。

5. **制約チェックと微調整**
   * 下側円弧のキー数制限を検証（最下段除外）。
   * 近接衝突があれば、`snap_corner()` の目標を微調整しながら再適用（角接触は維持）。

*参考・極小疑似コード*
```python
for r in rows:
    dθ = 2*asin(P[r]/(2*R[r]))
    for sec in sections[r]:
        if sec.type == "H":
            place_horizontal(sec)  # 回転=0°, 必要なら角スナップ
        else:
            θ = sec.θ0
            prev = None
            for c in sec.cols:
                fp = get_switch(r,c)
                place_on_arc(fp, C, R[r], θ)
                orient_to_tangent(fp, θ, sec.orientation)
                if prev:
                    snap_corner(fp, 'center_side', target=(prev, 'center_side'))
                prev = fp
                θ += dθ
    validate_lower_arc_limit(r)
```

---

## 要点（API仕様の勘所）

* **関数契約（要旨）**
  * `place_on_arc(fp, C, R, theta)`  
    * 入力：フットプリント `fp`、中心 `C`、半径 `R`、角 `theta`（rad）  
    * 効果：`fp` の原点（中心）を `C + R*(cosθ, sinθ)` に移動（座標系の上下向きに応じて `sinθ` 符号に注意）
  * `orient_to_tangent(fp, theta, orientation, y_up=True)`  
    * 入力：角 `theta`、`orientation ∈ {UPPER, LOWER}`、`y_up` は座標系の上向き  
    * 効果：接線方向に回転。一般式 `φ = θ + ( +90° if UPPER else -90° )`（`y_up=False` なら符号反転）
  * `snap_corner(fp, which, target)`  
    * 入力：`which ∈ {'center_side', 'NE','NW','SE','SW'}`、`target` は座標点 or `(fpB, whichB)`  
    * 効果：指定角をターゲットに一致させる平行移動（回転は変えない）

* **数値安定化**
  * `pitch/(2R) ≤ 1` を必ず満たすように `R` を設定（`asin` の定義域を確保）。
  * 円弧–水平の境界は **角度と接線方向が連続** になるよう `θ0` を決めると段差が出ない。
  * 角接触後に生じる微小ズレは、最後に水平区間へ影響が伝播しないよう区間内で吸収。

* **設計のコツ**
  * 行ごとの `R[r]` は **等差** または **等比** いずれでもよいが、視覚連続性は等差が扱いやすい。
  * 「中心側角」の自動判定は、仮回転後に4隅の距離 `||corner - C||` が最小の角を選べば安定。
  * 横長キーの中心側角は、**短辺方向にある2角のうち C に近い方** を選択すると一貫する。
