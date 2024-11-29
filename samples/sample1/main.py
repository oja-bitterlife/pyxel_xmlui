# 今回はpyxel向けのライブラリを作るのです
import pyxel

# ui_code内で作ったUIライブラリのインスタンスを持ってくる
from .ui_code import xmlui

# ここからゲーム本体開始
# *********************************************************
pyxel.init(256, 256)

# Main
def update(): # フレームの更新処理
    # ゲームの更新コード

    # UI更新
    xmlui.check_input_on(pyxel.btn)
    xmlui.update()

    # デバッグ
    if xmlui.debug.is_lib_debug:
        if pyxel.btnp(pyxel.KEY_T):
            print(xmlui.strtree())

def draw(): # 描画処理
    # ゲームの描画コード
    pyxel.cls(0)

    # UI描画
    xmlui.draw()

# アプリケーションの実行
def run():
    pyxel.run(update, draw)