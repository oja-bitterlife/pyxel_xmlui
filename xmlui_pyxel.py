from xmlui import XMLUI,UI_STATE,UI_EVENT,UI_CURSOR,UI_PAGE_TEXT

ui_template = XMLUI.createFromFile("assets/ui/test.xml")

import pyxel
font = pyxel.Font("assets/font/b12.bdf")
FONT_SIZE = 12


def my_ui_update(state: UI_STATE, event:UI_EVENT):
    # メインメニューを開く
    if "action" in event.trg:
        state.open(ui_template, "menu_command")


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


def msg_win_update(state: UI_STATE, event:UI_EVENT):
    msg_cur = state.findByTag("msg_cur")
    msg_text = state.findByTag("msg_text")

    # 文字列更新
    wrap = msg_text.attrInt("wrap", 1024)
    text = UI_PAGE_TEXT(msg_text, "draw_count").bind({"name":"world", "age":10}, wrap).next()
    page = text.usePage("page_no", 3)

    # カーソル表示
    msg_cur.setAttr("visible", not page.is_pages_end)  # 次のページあり

    if "action" in event.trg:
        if page.is_pages_end:
            state.close("menu_command")  # メニューごと閉じる
        else:
            # テキストを表示しきっていたら
            if page.is_page_finish:
                page.next()  # 次のページ
            # テキストがまだ残っていたら
            else:
                text.finish()  # 一気に表示

    # メニューごと閉じる
    if "cancel" in event.trg:
        state.close("menu_command")


# update関数テーブル
updateFuncs= {
    'my_ui': my_ui_update,
    "menu_win": menu_win_update,
    "msg_win": msg_win_update,
}


def msg_win_draw(state:UI_STATE):
    frame_color = state.attrInt("frame_color", 7)
    pyxel.rect(state.area.x, state.area.y, state.area.w, state.area.h, 12)
    pyxel.rectb(state.area.x, state.area.y, state.area.w, state.area.h, frame_color)
    pyxel.rectb(state.area.x+1, state.area.y+1, state.area.w-2, state.area.h-2, frame_color)
    pyxel.rectb(state.area.x+3, state.area.y+3, state.area.w-6, state.area.h-6, frame_color)

def msg_text_draw(state:UI_STATE):
    wrap = state.attrInt("wrap", 1024)

    # テキスト表示
    text = UI_PAGE_TEXT(state, "draw_count").bind({"name":"world", "age":10}, wrap)
    page = text.usePage("page_no", 3)

    for i,text in enumerate(page.splitPage()):
        pyxel.text(state.area.x, state.area.y+i*FONT_SIZE, text, 7, font)

def msg_cur_draw(state:UI_STATE):
    tri_size = state.attrInt("size", 6)
    color = state.attrInt("color", 7)

    # カーソル表示
    x, y = state.area.x, state.area.y
    pyxel.tri(x, y, x+tri_size, y, x+tri_size//2, y+tri_size//2, color)

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

def menu_item_draw(state:UI_STATE):
    color = state.attrInt("color", 7)
    pyxel.text(state.area.x, state.area.y, state.text, color, font)

def menu_cur_draw(state:UI_STATE):
    tri_size = state.attrInt("size", 6)
    color = state.attrInt("color", 7)

    # カーソル表示
    x = state.area.x
    y = state.area.y
    pyxel.tri(x, y, x, y+tri_size, x+tri_size//2, y+tri_size//2, color)

# draw関数テーブル
drawFuncs= {
    "msg_win": msg_win_draw,
    "msg_text": msg_text_draw,
    "msg_cur": msg_cur_draw,
    "menu_win": menu_win_draw,
    "menu_item": menu_item_draw,
    "menu_cur": menu_cur_draw,
}


# 処理関数の登録
def setDefaults(xmlui: XMLUI):
    for key in drawFuncs:
        xmlui.setDrawFunc(key, drawFuncs[key])

    for key in updateFuncs:
        xmlui.setUpdateFunc(key, updateFuncs[key])
