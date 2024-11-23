from xmlui import XMLUI,UI_STATE,UI_EVENT,UI_CURSOR


from typing import Callable,Any
from functools import wraps

ui_template = XMLUI.createFromFile("assets/ui/test.xml")
ui_worker = XMLUI.createWorker("my_ui")

import pyxel
font = pyxel.Font("assets/font/b12.bdf")
FONT_SIZE = 12


# 入力待ち
# *****************************************************************************
@ui_worker.tag_update("my_ui")
def my_ui_update(state: UI_STATE, event:UI_EVENT):
    # メインメニューを開く
    if "action" in event.trg:
        state.open(ui_template, "menu_command")


# コマンドメニュー
# *****************************************************************************
# 更新
# ---------------------------------------------------------
@ui_worker.tag_update("menu_win")
def menu_win_update(state: UI_STATE, event:UI_EVENT):
    item_w, item_h = state.attrInt("item_w"), state.attrInt("item_h")

    # メニューアイテム取得
    grid = state.arrayByTag("menu_row", "menu_item")

    # 各アイテムの位置設定
    for y,cols in enumerate(grid):
        for x,rows in enumerate(cols):
            rows.setAttr(["x", "y"], (x*item_w, y*item_h))

    # カーソル
    cursor = UI_CURSOR(state.findByTag("menu_cur"), len(grid[0]), len(grid)).moveByEvent(event.trg, "left", "right", "up", "down")
    cursor.state.setAttr(["x", "y"], (cursor.cur_x*item_w-6, cursor.cur_y*item_h+2))  # 表示位置設定

    # 選択アイテムの表示
    if "action" in event.trg:
        # メッセージウインドウ表示
        state.open(ui_template, "win_message")

    # 閉じる
    if "cancel" in event.trg:
        state.close(state.id)


# 描画
# ---------------------------------------------------------
@ui_worker.tag_draw("menu_win")
def menu_win_draw(state:UI_STATE):
    bg_color = state.attrInt("bg_color", 12)
    frame_color = state.attrInt("frame_color", 7)
    title  = state.attrStr("title", "")

    pyxel.rect(state.area.x, state.area.y, state.area.w, state.area.h, bg_color)
    pyxel.rectb(state.area.x, state.area.y, state.area.w, state.area.h, frame_color)
    pyxel.rectb(state.area.x+1, state.area.y+1, state.area.w-2, state.area.h-2, frame_color)

    if title:
        str_w = FONT_SIZE*len(title)
        text_x = state.area.x+(state.area.w-str_w)/2
        pyxel.rect(text_x,state.area.y, str_w, FONT_SIZE, bg_color)
        pyxel.text(text_x, state.area.y-2, title, frame_color, font)

@ui_worker.tag_draw("menu_item")
def menu_item_draw(state:UI_STATE):
    color = state.attrInt("color", 7)
    pyxel.text(state.area.x, state.area.y, state.text, color, font)

@ui_worker.tag_draw("menu_cur")
def menu_cur_draw(state:UI_STATE):
    tri_size = state.attrInt("size", 6)
    color = state.attrInt("color", 7)

    # カーソル表示
    x = state.area.x
    y = state.area.y
    pyxel.tri(x, y, x, y+tri_size, x+tri_size//2, y+tri_size//2, color)


# メッセージウインドウ
# *****************************************************************************
# 更新
# ---------------------------------------------------------
@ui_worker.tag_update("msg_win")
def msg_win_update(state: UI_STATE, event:UI_EVENT):
    msg_cur = state.findByTag("msg_cur")
    msg_text = state.findByTag("msg_text")

    # 文字列更新
    wrap = msg_text.attrInt("wrap", 1024)
    text = msg_text.getAnimText("draw_count").bind({"name":"world", "age":10}, wrap).next(0.1)
    page = text.usePage("page_no", 3)

    # カーソル表示
    msg_cur.setAttr("visible", not page.is_end_page and page.is_finish)  # 次のページあり

    if "action" in event.trg:
        if page.is_end_page:
            state.close("menu_command")  # メニューごと閉じる
        else:
            # テキストを表示しきっていたら
            if page.is_finish:
                page.nextPage()  # 次のページ
            # テキストがまだ残っていたら
            else:
                text.finish()  # 一気に表示

    # メニューごと閉じる
    if "cancel" in event.trg:
        state.close("menu_command")


# 描画
# ---------------------------------------------------------
@ui_worker.tag_draw("msg_win")
def msg_win_draw(state:UI_STATE):
    frame_color = state.attrInt("frame_color", 7)
    pyxel.rect(state.area.x, state.area.y, state.area.w, state.area.h, 12)
    pyxel.rectb(state.area.x, state.area.y, state.area.w, state.area.h, frame_color)
    pyxel.rectb(state.area.x+1, state.area.y+1, state.area.w-2, state.area.h-2, frame_color)
    pyxel.rectb(state.area.x+3, state.area.y+3, state.area.w-6, state.area.h-6, frame_color)

@ui_worker.tag_draw("msg_text")
def msg_text_draw(state:UI_STATE):
    # テキスト表示
    wrap = state.attrInt("wrap", 1024)
    text = state.getAnimText("draw_count").bind({"name":"world", "age":10}, wrap)
    page = text.usePage("page_no", 3)

    for i,text in enumerate(page.split()):
        pyxel.text(state.area.x, state.area.y+i*FONT_SIZE, text, 7, font)

@ui_worker.tag_draw("msg_cur")
def msg_cur_draw(state:UI_STATE):
    tri_size = state.attrInt("size", 6)
    color = state.attrInt("color", 7)

    # カーソル表示
    x, y = state.area.x, state.area.y
    pyxel.tri(x, y, x+tri_size, y, x+tri_size//2, y+tri_size//2, color)

