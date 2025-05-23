from typing import Callable

from xmlui.core import XMLUI,XUEvent,XURect
from xmlui.ext.tilemap import XUETileAnim, XUETileSet
from xmlui.ext.scene import XUEActItem

class PlayerMoveAct(XUEActItem):
    def __init__(self, player:"Player", move_x:int, move_y:int):
        super().__init__()
        self.player = player
        self.move_x = move_x
        self.move_y = move_y

    def waiting(self):
        # プレイヤの移動
        if self.move_x < 0:
            self.player.x -= 1
            self.move_x += 1
        if self.move_x > 0:
            self.player.x += 1
            self.move_x -= 1
        if self.move_y < 0:
            self.player.y -= 1
            self.move_y += 1
        if self.move_y > 0:
            self.player.y += 1
            self.move_y -= 1

        # 移動完了
        if self.move_x == 0 and self.move_y == 0:
            self.finish()

class Player:
    def __init__(self, xmlui:XMLUI, x:int, y:int):
        self.xmlui = xmlui

        # 座標
        self.x = x*16
        self.y = y*16
        self.move_x = 0
        self.move_y = 0

        # 表示イメージ設定
        self.tile = XUETileAnim(XUETileSet(1, [XURect(0, 32, 16, 16), XURect(16, 32, 16,16)]), [0, 1])

    def move(self, hitcheck_funcs:list[Callable[[int,int],bool]]):
        event = self.xmlui.event
        if event.check_now(XUEvent.Key.UP) and all([not hit(self.block_x, self.block_y-1) for hit in hitcheck_funcs]):
            return PlayerMoveAct(self, 0, -16)
        if event.check_now(XUEvent.Key.DOWN) and all([not hit(self.block_x, self.block_y+1) for hit in hitcheck_funcs]):
            return PlayerMoveAct(self, 0, 16)
        if event.check_now(XUEvent.Key.LEFT) and all([not hit(self.block_x-1, self.block_y) for hit in hitcheck_funcs]):
            return PlayerMoveAct(self, -16, 0)
        if event.check_now(XUEvent.Key.RIGHT) and all([not hit(self.block_x+1, self.block_y) for hit in hitcheck_funcs]):
            return PlayerMoveAct(self, 16, 0)
        return None

    @property
    def is_moving(self) -> bool:
        return self.move_x != 0 or self.move_y != 0

    @property
    def block_x(self) -> int:
        return self.x // 16

    @property
    def block_y(self) -> int:
        return self.y // 16

    def draw(self):
        self.tile.update()
        self.tile.draw(127, 127-8)
