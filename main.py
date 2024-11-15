import pyxel # Pyxelモジュールをインポート

pyxel.init(256, 256) # 初期化(ウィンドウサイズを指定)

def update(): # フレームの更新処理
    if pyxel.btnp(pyxel.KEY_Q):
        pyxel.quit()

    xmlui.update()

def draw(): # 描画処理
    pyxel.cls(0)

    # UI描画
    xmlui.draw()

from xmlui import XMLUI
xmlui = XMLUI.createFromFile("assets/ui/test.xml")


import xmlui_pyxel
xmlui_pyxel.setDefaults(xmlui)


msg_win = xmlui.findByTag("msg_win")
if msg_win != None:
    msg_win2 = msg_win.duplicate()
    msg_win2.setAttr("y", 100)
    msg_win2.setAttr("w", 100)
    xmlui.root.append_list.append(msg_win2)

# アプリケーションの実行
pyxel.run(update, draw)
