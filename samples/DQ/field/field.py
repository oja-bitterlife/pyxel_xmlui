import pyxel

# タイトル画面
from xmlui.core import XMLUI,XUEvent,XUWinBase,XUSelectItem,XURect
from xmlui.lib import select,text
from xmlui_ext import dq

import db
from ui_common import system_font,input_def

from field.player import Player
from field.bg import BG
from field.npc import NPC
from field.treasure import Treasure


class Field:
    def __init__(self, xmlui:XMLUI):
        self.xmlui = xmlui

        # ゲーム本体(仮)
        self.player = Player(10, 10)
        self.bg = BG()
        self.npc = NPC()
        self.treasure = Treasure()

        self.goto_battle = False

        # UIの読み込み
        self.template = self.xmlui.load_template("assets/ui/field.xml")
        ui_init(self.template)

    def __del__(self):
        # 読みこんだUIの削除
        self.template.remove()

    def update(self):
        # UIメニューが開いていたらキャラが動かないように
        if not self.xmlui.exists_id("menu"):
            # プレイヤの移動
            self.player.update(self.bg.blocks, self.npc.npc_data)

            # キャラが動いていなければメニューオープン可能
            if not self.player.is_moving:
                self.xmlui.open_by_event(input_def.BTN_A, "menu")

        else:
            menu = self.xmlui.find_by_id("menu")
            # 会話イベントチェック
            self.npc.check_talk(menu, self.player)
            self.bg.check_door(menu, self.player)
            self.bg.check_stairs(menu, self.player)

        # バトル開始
        if "start_battle" in self.xmlui.event.trg:
            self.goto_battle = True
        if self.goto_battle:
            # メニューが開いていない状態まで待つ
            if not self.xmlui.exists_id("menu") or XUWinBase(self.xmlui.find_by_id("menu")).win_state == XUWinBase.STATE_CLOSED:
                return "battle"

    def draw(self):
        # プレイヤを中心に世界が動く。さす勇
        scroll_x = -self.player.x +160-32
        scroll_y = -self.player.y +160-32-8

        # ゲーム画面構築
        self.bg.draw(scroll_x, scroll_y)
        self.npc.draw(scroll_x, scroll_y)
        self.treasure.draw(scroll_x, scroll_y)
        self.player.draw()

        # UIの描画(fieldとdefaultグループ)
        self.xmlui.draw()


# 町の中UI
# *****************************************************************************
from ui_common import draw_menu_cursor, get_world_clip, common_msg_text

def ui_init(template):
    # fieldグループ用デコレータを作る
    field_select = select.Decorator(template)
    field_text = text.Decorator(template)
    field_dq = dq.Decorator(template)

    # ラベル
    # ---------------------------------------------------------
    # コマンドメニューのタイトル
    @field_text.label("title", "align", "valign")
    def title(title:text.Label, event:XUEvent):
        clip = get_world_clip(XUWinBase.find_parent_win(title)).intersect(title.area)
        pyxel.rect(title.area.x, title.area.y, title.area.w, clip.h, 0)  # タイトルの下地

        # テキストはセンタリング
        if title.area.y < clip.bottom():  # world座標で比較
            x, y = title.aligned_pos(system_font)
            pyxel.text(x, y-1, title.text, 7, system_font.font)

    # 各メニューごとのタイトル(コマンドメニューと少し場所がずれる)
    @field_text.label("menu_item_title", "align", "valign")
    def menu_item_title(menu_item_title:text.Label, event:XUEvent):
        clip = get_world_clip(XUWinBase.find_parent_win(menu_item_title)).intersect(menu_item_title.area)
        clip.h = max(clip.h, 4)  # フレームを隠すように
        pyxel.rect(menu_item_title.area.x, menu_item_title.area.y, menu_item_title.area.w, clip.h, 0)  # タイトルの下地

        # テキストはセンタリングで常に表示
        x, y = menu_item_title.aligned_pos(system_font)
        pyxel.text(x, y-1, menu_item_title.text, 7, system_font.font)

    # コマンドメニュー
    # ---------------------------------------------------------
    def menu_item(menu_item:XUSelectItem):
        # ウインドウのクリップ状態に合わせて表示する
        if menu_item.area.y < get_world_clip(XUWinBase.find_parent_win(menu_item)).bottom():
            pyxel.text(menu_item.area.x+6, menu_item.area.y, menu_item.text, 7, system_font.font)

            # カーソル表示
            if menu_item.selected and menu_item.enable:
                draw_menu_cursor(menu_item, 0, 0)

    @field_select.grid("menu_grid", "menu_item")
    def menu_grid(menu_grid:select.Grid, event:XUEvent):
        # 各アイテムの描画
        for item in menu_grid.items:
            menu_item(item)

        # メニュー選択
        menu_grid.select_by_event(event.trg, *input_def.CURSOR)

        # 選択アイテムの表示
        if input_def.BTN_A in event.trg:
            match menu_grid.action:
                case "talk":
                    menu_grid.open("talk_dir")
                case "tools":
                    menu_grid.open("tools")
                case "stairs":
                    return "down_stairs"
                case "door":
                    return "open_door"
                case _:
                    menu_grid.xmlui.popup("under_construct")

        # アイテムの無効化(アイテムカーソル用)
        is_message_oepn = menu_grid.xmlui.exists_id("message")
        for item in menu_grid.items:
            item.enable = event.is_active and not is_message_oepn

        # 閉じる
        if input_def.BTN_B in event.trg:
            XUWinBase.find_parent_win(menu_grid).start_close()

    # 会話方向
    # ---------------------------------------------------------
    def dir_item(dir_item:XUSelectItem):
        # ウインドウのクリップ状態に合わせて表示する
        if dir_item.area.y < get_world_clip(XUWinBase.find_parent_win(dir_item)).bottom():
            pyxel.text(dir_item.area.x, dir_item.area.y, dir_item.text, 7, system_font.font)

        # カーソル表示
        if dir_item.selected and dir_item.enable:
            draw_menu_cursor(dir_item, -5, 0)

    @field_select.list("dir_select", "dir_item")
    def dir_select(dir_select:select.List, event:XUEvent):
        # 各アイテムの描画
        for item in dir_select.items:
            dir_item(item)

        # 会話ウインドウは特別な配置
        if input_def.UP in event.trg:
            dir_select.select(0)
        if input_def.LEFT in event.trg:
            dir_select.select(1)
        if input_def.RIGHT in event.trg:
            dir_select.select(2)
        if input_def.DOWN in event.trg:
            dir_select.select(3)

        if input_def.BTN_A in event.trg:
            dir_win = XUWinBase.find_parent_win(dir_select)
            dir_win.start_close()
            return f"start_talk_{dir_select.action}"

        # 閉じる
        if input_def.BTN_B in event.trg:
            XUWinBase.find_parent_win(dir_select).start_close()


    # どうぐメニュー
    # ---------------------------------------------------------
    def tools_item(tools_item:XUSelectItem):
        # ウインドウのクリップ状態に合わせて表示する
        if tools_item.area.y < get_world_clip(XUWinBase.find_parent_win(tools_item)).bottom():
            pyxel.text(6+tools_item.area.x, tools_item.area.y, tools_item.text, 7, system_font.font)

        # カーソル表示
        if tools_item.selected and tools_item.enable:
            draw_menu_cursor(tools_item, 0, 0)

    @field_select.list("tools_list", "tools_item")
    def tools_list(tools_list:select.List, event:XUEvent):
        # 各アイテムの描画
        for item in tools_list.items:
            tools_item(item)

        tools_list.select_by_event(event.trg, *input_def.UP_DOWN)

        if input_def.BTN_A in event.trg:
            if tools_list.action == "herbs":
                db.user_data.hp += 10
                XUWinBase.find_parent_win(tools_list).start_close()

                # メッセージウインドウを開く
                msg_win = tools_list.xmlui.find_by_id("menu").open("message")
                msg_text = dq.MsgDQ(msg_win.find_by_id("msg_text"))
                msg_text.append_msg("ＨＰが　１０かいふくした")  # systemメッセージ
            else:
                tools_list.xmlui.popup("under_construct")
        
        # 閉じる
        if input_def.BTN_B in event.trg:
            XUWinBase.find_parent_win(tools_list).start_close()


    # フィールド画面のメッセージウインドウ
    # ---------------------------------------------------------
    @field_dq.msg_dq("msg_text")
    def msg_text(msg_text:dq.MsgDQ, event:XUEvent):
        # メッセージ共通処理
        common_msg_text(msg_text, event, True)

        # 自分が閉じたらメニューごと閉じる
        if XUWinBase.find_parent_win(msg_text).win_state == XUWinBase.STATE_CLOSED:
            XUWinBase(msg_text.xmlui.find_by_id("menu")).start_close()

        # 入力アクション
        # ---------------------------------------------------------
        if input_def.BTN_A in event.trg or input_def.BTN_B in event.now:
            if msg_text.is_all_finish:
                XUWinBase.find_parent_win(msg_text).start_close()  # 閉じる
                return

        if input_def.BTN_A in event.trg or input_def.BTN_B in event.now:
            if msg_text.is_next_wait:
                msg_text.set_page_no(msg_text.page_no+1)  # 次ページへ
                return
