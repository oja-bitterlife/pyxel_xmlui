import pyxel

from xmlui.core import XMLUI,XUEvent,XUWinInfo,XUSelectItem,XUTextUtil,XUElem
from xmlui.lib import select

from msg_dq import MsgDQ
from system_dq import system_font
from ui_common import get_world_clip,draw_menu_cursor,get_text_color

from db import user_data,tools_data

def ui_init(xmlui:XMLUI):
    field_select = select.Decorator(xmlui)

    # どうぐメニュー
    # *************************************************************************
    # どうぐリストアイテム
    def tools_item(tools_item:XUSelectItem):
        col = get_text_color()

        # ウインドウのクリップ状態に合わせて表示する
        if tools_item.area.y < get_world_clip(XUWinInfo.find_parent_win(tools_item)).bottom:
            pyxel.text(6+tools_item.area.x, tools_item.area.y, tools_item.text, col, system_font.font)

        # カーソル表示
        if tools_item.selected and tools_item.enable:
            draw_menu_cursor(tools_item, 0, 0)

    # どうぐ選択リスト
    @field_select.list("tools_list", "tools_item")
    def tools_list(tools_list:select.XUList, event:XUEvent):
        # アイテム表示の準備
        if event.on_init:  # 開く度毎回
            for tools in user_data.tools:
                tools_list.add_child(XUElem.new(tools_list.xmlui, "tools_item").set_text(tools).set_attr("action", tools))

        # 各アイテムの描画
        for item in tools_list.items:
            tools_item(item)

        tools_list.select_by_event(event.trg, *XUEvent.Key.UP_DOWN())

        # どうぐを使用した
        # ---------------------------------------------------------
        if event.check_trg(XUEvent.Key.BTN_A):
            # どうぐデータ取得
            try:
                data = tools_data.get_data(tools_list.selected_item.action)
            except:
                tools_list.xmlui.popup("under_construct")
                return

            # 効果発現
            msg = tools_effect(tools_list.selected_no, data)

            # メッセージウインドウを開く
            XUWinInfo.find_parent_win(tools_list).setter.close()
            msg_win = tools_list.xmlui.find_by_id("menu").open("message")
            msg_text = MsgDQ(msg_win.find_by_id("msg_text"))
            msg_text.append_msg(msg)  # systemメッセージ

        # 閉じる
        # ---------------------------------------------------------
        if event.check_trg(XUEvent.Key.BTN_B):
            XUWinInfo.find_parent_win(tools_list).setter.close()


    # どうぐ処理
    # *************************************************************************
    def tools_effect(selected_no:int, data) -> str:
        match data["type"]:
            case "やくそう":
                value = data["value"]
                user_data.hp += value
                tools_remove(selected_no)
                return XUTextUtil.format_zenkaku(data["msg"], {"value":value})

        return "なにもおこらなかった"

    # 消費
    def tools_remove(selected_no:int):
        user_data.tools.pop(selected_no)
