# タイトル画面
from xmlui.core import XMLUI
from title.ui import start,speed

class Title:
    NEXT_SCENE_EVENT = "game_start"

    def __init__(self, xmlui:XMLUI):
        self.xmlui = xmlui

        # XMLの読み込み
        self.template = self.xmlui.load_template("assets/ui/title.xml")
        self.xmlui.open("game_title")  # game_title以下表示開始

        # ui初期化
        start.ui_init(self.template)
        speed.ui_init(self.template)

    def __del__(self):
        # XMLの解放
        self.template.remove()

    def update(self):
        # 次のシーンへ
        if self.NEXT_SCENE_EVENT in self.xmlui.event.trg:
            return "field"

    def draw(self):
        # UIの表示
        self.xmlui.draw()
