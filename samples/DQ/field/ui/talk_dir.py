import pyxel

from xmlui.core import XMLUI,XUEvent,XUWinInfo,XUSelectItem
from xmlui.lib import select

from system_dq import system_font
from ui_common import get_world_clip,draw_menu_cursor,get_text_color

def ui_init(xmlui:XMLUI):
    field_select = select.Decorator(xmlui)

    # 会話方向
    # ---------------------------------------------------------
    def dir_item(dir_item:XUSelectItem):
        col = get_text_color()

        # ウインドウのクリップ状態に合わせて表示する
        if dir_item.area.y < get_world_clip(XUWinInfo.find_parent_win(dir_item)).bottom:
            pyxel.text(dir_item.area.x, dir_item.area.y, dir_item.text, col, system_font.font)

        # カーソル表示
        if dir_item.selected and dir_item.enable:
            draw_menu_cursor(dir_item, -5, 0)

    @field_select.list("dir_select", "dir_item")
    def dir_select(dir_select:select.XUList, event:XUEvent):
        # 各アイテムの描画
        for item in dir_select.items:
            dir_item(item)

        # 会話ウインドウは特別な配置
        if event.check_trg(XUEvent.Key.UP):
            dir_select.select(0)
        elif event.check_trg(XUEvent.Key.LEFT):
            dir_select.select(1)
        elif event.check_trg(XUEvent.Key.RIGHT):
            dir_select.select(2)
        elif event.check_trg(XUEvent.Key.DOWN):
            dir_select.select(3)

        if event.check_trg(XUEvent.Key.BTN_A):
            dir_win = XUWinInfo.find_parent_win(dir_select)
            dir_win.setter.close()
            dir_win.on(f"start_talk_{dir_select.selected_item.action}")

        # 閉じる
        if event.check_trg(XUEvent.Key.BTN_B):
            XUWinInfo.find_parent_win(dir_select).setter.close()
