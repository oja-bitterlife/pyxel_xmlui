import pyxel

from xmlui.core import XMLUI,XUEvent,XUEventItem,XUWinInfo
from xmlui.lib.debug import DebugXMLUI
from xmlui.ext.scene import XUEFadeScene,XUEActItem

from db import user_data

# フィールド関係
from field.modules.player import Player
from field.modules.bg import BG
from field.modules.npc import NPCManager
from field.modules.field_obj import FieldObj

# UI
import ui_common
from msg_dq import MsgDQ
from field.ui import msg_win,menu,talk_dir,tools

# メニューが開いている状態
class MenuOpenAct(XUEActItem):
    def __init__(self, xmlui:XMLUI):
        super().__init__()
        self.menu = xmlui.open("menu")

    # メニューが閉じられるまで待機
    def waiting(self):
        if self.menu.removed:
            self.finish()

class Field(XUEFadeScene):
    def __init__(self):
        super().__init__(DebugXMLUI(pyxel.width, pyxel.height))

        # UIの読み込み
        self.xmlui.load_template("assets/ui/field.xml")
        self.xmlui.load_template("assets/ui/common.xml")

        ui_common.ui_init(self.xmlui)
        msg_win.ui_init(self.xmlui)
        menu.ui_init(self.xmlui)
        talk_dir.ui_init(self.xmlui)
        tools.ui_init(self.xmlui)

        # ゲーム本体(仮)
        self.player = Player(self.xmlui, 10, 10)
        self.bg = BG()
        self.npc = NPCManager()
        self.field_obj = FieldObj()

        # 画像読み込み
        pyxel.images[1].load(0, 0, "assets/images/field_tile.png" )

    # 死亡でFieldに飛ばされた
    @classmethod
    def create_with_dead(cls) -> "Field":
        self = cls()

        user_data.hp = 1
        self.player.x = 8*16
        self.player.y = 9*16

        # メッセージウインドウを開く
        self.add_act(MenuOpenAct(self.xmlui))
        msg_text = MsgDQ(self.xmlui.find_by_id("menu").open("message").find_by_id("msg_text"))
        talk = "おお　{name}！\nしんでしまうとは　なにごとだ！\\p…………\\pちょっと　いってみたかったの\\pがんばってね"
        msg_text.append_talk(talk, user_data.data)  # talkでテキスト開始

        return self

    def closed(self):
        self.xmlui.close()  # 読みこんだUIの削除

        # バトルへ
        from battle import Battle
        self.set_next_scene(Battle())

    # 何もしていない(actがない)ときだけここにくる、Idle関数
    def idle(self):
        # メニューオープン
        if self.xmlui.event.check_now(XUEvent.Key.BTN_A):
            self.add_act(MenuOpenAct(self.xmlui))
            return

        # プレイヤの移動
        hit_list = [self.npc.hit_check, self.bg.hit_check, self.field_obj.hit_check]  # 当たり判定リスト
        player_move_act = self.player.move(hit_list)  # 当たり判定。移動できれば移動Actが返る
        if player_move_act:
            self.add_act(player_move_act)
            return

    def draw(self):
        # プレイヤを中心に世界が動く。さす勇
        scroll_x = -self.player.x +160-32
        scroll_y = -self.player.y +160-32-8

        # ゲーム画面構築
        self.bg.draw(scroll_x, scroll_y)
        self.npc.draw(scroll_x, scroll_y)
        self.field_obj.draw(scroll_x, scroll_y)
        self.player.draw()

        # UIの描画(fieldとdefaultグループ)
        self.xmlui.draw()

    # メニューで起こったイベントの処理を行う
    def event(self, event:XUEventItem):
        # コマンドメニューイベント
        # -------------------------------------------------
        if event.name.startswith("cmd_"):
            menu_win = XUWinInfo(self.xmlui.find_by_id("menu"))
            match event.name:
                case "cmd_stairs":
                    if self.bg.check_stairs(self.player.block_x, self.player.block_y):
                        # バトル開始
                        menu_win.setter.close()
                        self.close()
                    else:
                        msg_text = MsgDQ(menu_win.open("message").find_by_id("msg_text"))
                        msg_text.append_msg("かいだんがない")  # systemメッセージ
                case "cmd_door":
                    door = self.field_obj.find_door(self.player.block_x, self.player.block_y)
                    if door and not self.field_obj.is_opened(door):
                        self.field_obj.open(door)
                        menu_win.setter.close()
                    else:
                        msg_text = MsgDQ(menu_win.open("message").find_by_id("msg_text"))
                        msg_text.append_msg("とびらがない")  # systemメッセージ
                case _:
                    raise Exception("unknown cmd")
            return

        # メッセージウインドウがcloseされた時はメニューごと閉じる
        if event.name == "round_win_closed" and event.sender.id == "message":
            menu_win = XUWinInfo(self.xmlui.find_by_id("menu"))
            menu_win.setter.close()
            return

        # 会話イベントチェック
        if event.name.startswith("start_talk_"):
            menu_win = XUWinInfo(self.xmlui.find_by_id("menu"))

            # メッセージウインドウを開く
            msg_text = MsgDQ(menu_win.open("message").find_by_id("msg_text"))

            # テキストの設定
            talk = self.npc.check_talk(event.name, self.player.block_x, self.player.block_y)
            if talk:
                msg_text.append_talk(talk, user_data.data)  # talkでテキスト開始
            else:
                msg_text.append_msg("だれもいません")  # systemメッセージ
