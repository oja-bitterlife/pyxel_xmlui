import pyxel # Pyxelモジュールをインポート

pyxel.init(256, 256) # 初期化(ウィンドウサイズを指定)

from xmlui import XMLUI
xmlui = XMLUI.createFromFile("assets/ui/test.xml")

# お試しサンプルUI
import xmlui_pyxel
xmlui_pyxel.setDefaults(xmlui)

from xmlui import UI_MENU
command_item_data = [
    ["speak", "tool"],
    ["status", "check"],
]

command_win = xmlui.findByID("command_win")
if command_win:
    command_items = UI_MENU(command_item_data, command_win, 0, 0)
    command_win.userData["item_data"] = command_items


# Main
def update(): # フレームの更新処理
    if pyxel.btnp(pyxel.KEY_Q):
        pyxel.quit()

    if pyxel.btnp(pyxel.KEY_LEFT):
        command_items.moveLeft()
    if pyxel.btnp(pyxel.KEY_RIGHT):
        command_items.moveRight()
    if pyxel.btnp(pyxel.KEY_UP):
        command_items.moveUp()
    if pyxel.btnp(pyxel.KEY_DOWN):
        command_items.moveDown()

    if pyxel.btnp(pyxel.KEY_SPACE):
        if command_items.getData() == "speak":
            msg_text = xmlui.findByTag("msg_text")
            if msg_text:
                msg_text.update_count = 0

    xmlui.update()

def draw(): # 描画処理
    pyxel.cls(0)

    # UI描画
    xmlui.draw()

# アプリケーションの実行
pyxel.run(update, draw)
