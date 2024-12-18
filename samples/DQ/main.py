# 今回はpyxel向けのライブラリを作るのです
import pyxel

# ここからゲーム本体開始
# *********************************************************
pyxel.init(256, 256)

from xmlui.core import XUEvent
from ui_common import xmlui
from xmlui.ext.scene import XUXScene

# 最初はタイトル
from title import Title
from field import Field
from battle import Battle

#XUXScene.current_scene = Title(xmlui)
XUXScene.current_scene = Field(xmlui)
#XUXScene.current_scene = Battle(xmlui)

# Main
def update(): # フレームの更新処理
    # デバッグ用
    if pyxel.btnp(pyxel.KEY_TAB):
        print(xmlui.strtree())
    if pyxel.btnp(pyxel.KEY_F5):
        xmlui.reload_templates()

    # シーン更新
    if XUXScene.current_scene:
        XUXScene.current_scene.update_scene()


def draw(): # 描画処理
    # ゲームの描画コード
    pyxel.cls(0)

    # シーン描画
    if XUXScene.current_scene:
        XUXScene.current_scene.draw_scene()

# アプリケーションの実行
pyxel.run(update, draw)
