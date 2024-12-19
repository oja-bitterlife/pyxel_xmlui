import pyxel

# タイトル画面
from xmlui.core import XMLUI
from xmlui.ext.scene import XUXScene

from title.ui import start,speed
from field import Field  # 次シーン

class Title(XUXScene):
    NEXT_SCENE_EVENT = "game_start"

    def __init__(self, xmlui:XMLUI):
        super().__init__(xmlui, 0)

        # XMLの読み込み
        self.template = self.xmlui.load_template("assets/ui/title.xml")
        self.xmlui.open("game_title")  # game_title以下表示開始

        # ui初期化
        start.ui_init(self.template)
        speed.ui_init(self.template)

        self.img = pyxel.Image.from_image(filename="assets/images/title.png")

    def closed(self):
        self.template.remove()
        XUXScene.current_scene = Field(self.xmlui)

    def draw(self):
        # 背景絵
        pyxel.blt(0, 0, self.img, 0, 0, self.img.width, self.img.height)

        # UIの表示
        self.xmlui.draw()
        if "start" in self.xmlui.event.trg:  # startが実行された
            super().end_scene()

