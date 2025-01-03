import pyxel

# xmlui_pyxelの初期化
# *****************************************************************************
from xmlui.core import XMLUI,XUElem,XUEvent,XUWinBase,XURect,XUTextUtil
from xmlui.lib import text,win
from msg_dq import MsgDQ

from xmlui.ext.pyxel_util import PyxelFont,PyxelPalette
from db import system_info, user_data

system_font = PyxelFont("assets/font/b12.bdf")
system_palette = PyxelPalette()


# 共通定義
# *****************************************************************************
WIN_OPEN_SPEED   = 16
WIN_CLOSE_SPEED   = 32
KOJICHU_COL = 15


# 共通で使える関数
# *****************************************************************************
# カーソル描画
def draw_menu_cursor(state:XUElem, x:int, y:int):
    col = get_text_color()

    tri_size = 6
    left = state.area.x + x
    top = state.area.y+2 + y
    pyxel.tri(left, top, left, top+tri_size, left+tri_size//2, top+tri_size//2, col)

def draw_msg_cursor(state:XUElem, x:int, y:int):
    col = get_text_color()

    tri_size = 6
    center_x = 127-tri_size//2+x  # Xはど真ん中固定で
    y = state.area.y + tri_size - 3 + y
    pyxel.tri(center_x, y, center_x+tri_size, y, center_x+tri_size//2, y+tri_size//2, col)

def get_world_clip(win:XUWinBase) -> XURect:
    area = win.area
    if win.is_opening:
        clip_size = min(int(win.opening_count * WIN_OPEN_SPEED), area.h)
        area.h = clip_size
    else:
        clip_size = max(int(win.closing_count * WIN_CLOSE_SPEED), 0)
        area.h -= clip_size
    return area

# テキストカラー
def get_text_color() -> int:
    return 8 if user_data.hp <= 1 else 7

# テキストカラー
def get_shadow_color() -> int:
    return 2 if user_data.hp <= 1 else 13


# メッセージウインドウを共通で使う
# *****************************************************************************
def common_msg_text(msg_dq:MsgDQ, event:XUEvent, cursor_visible:bool):
    area = msg_dq.area  # areaは重いので必ずキャッシュ
    line_height = system_font.size + 5  # 行間設定
    page_line_num = msg_dq.attr_int(msg_dq.PAGE_LINE_NUM_ATTR)
    scroll_line_num = page_line_num + 1  # スクロールバッファサイズはページサイズ+1
    scroll_split = 3  # スクロールアニメ分割数

    # テキストが空
    if not msg_dq.pages:
        return
    
    # カウンタ操作
    # ---------------------------------------------------------
    # ボタンを押している間は速度MAX
    speed = system_info.msg_spd
    if XUEvent.Key.BTN_A in event.now or XUEvent.Key.BTN_B in event.now:
        speed = system_info.MsgSpd.FAST

    # カウンタを進める。必ず行端で一旦止まる
    remain_count = msg_dq.current_page.current_line_length - len(msg_dq.current_page.current_line)
    msg_dq.current_page.draw_count += min(remain_count, speed.value)

    # 行が完了してからの経過時間
    if msg_dq.is_line_end:
        over_count = msg_dq.attr_int("_over_count") + 1
        # ページ切り替えがあったらリセット
        if msg_dq.current_page_no != msg_dq.attr_int("_old_page", -1):
            over_count = 0
    else:
        over_count = 0

    # 更新
    msg_dq.set_attr("_over_count", over_count)
    msg_dq.set_attr("_old_page", msg_dq.current_page_no)

    # 表示バッファ
    # ---------------------------------------------------------
    scroll_info =  msg_dq.dq_scroll_lines(scroll_line_num)

    # スクロール
    shift_y = 0
    # ページが完了している
    if msg_dq.current_page.is_finish:
        # スクロールが必要？
        if len(scroll_info) > page_line_num:
            # スクロールが終わった
            if over_count >= scroll_split:
                scroll_info = scroll_info[1:]
            # スクロール
            else:
                shift_y = min(over_count,scroll_split) * line_height*0.8 / scroll_split

    # 行だけが完了している
    elif msg_dq.is_line_end:
        # スクロールが必要？
        if len(scroll_info) > page_line_num:
            # スクロールが終わった
            if over_count >= scroll_split:
                scroll_info = scroll_info[1:]
                msg_dq.current_page.draw_count = int(msg_dq.current_page.draw_count) + 1  # 次の文字へ
                msg_dq.set_attr("_over_count", 0)  # 最速表示対応
            # スクロール
            else:
                shift_y = min(over_count,scroll_split) * line_height*0.8 / scroll_split

        # スクロールが不要でも一瞬待機
        elif over_count >= scroll_split:
            msg_dq.current_page.draw_count = int(msg_dq.current_page.draw_count) + 1  # 次の文字へ
            msg_dq.set_attr("_over_count", 0)  # 最速表示対応


    # テキスト描画
    for i,info in enumerate(scroll_info):
        # yはスクロール考慮
        y = area.y + i*line_height - shift_y
        clip = get_world_clip(XUWinBase.find_parent_win(msg_dq)).intersect(msg_dq.area)
        if y+system_font.size >= clip.bottom():  # メッセージもクリップ対応
            break

        # インデント設定
        x = area.x
        if info.indent_type == MsgDQ.IndentType.TALK:
            x += system_font.text_width(MsgDQ.TALK_START)
        elif info.indent_type == MsgDQ.IndentType.ENEMY:
            x += system_font.size

        col = get_text_color()
        pyxel.text(x, y, info.line_text, col, system_font.font)


    # カーソル表示
    # ---------------------------------------------------------
    if cursor_visible and msg_dq.is_next_wait and shift_y == 0:  # ページ送り待ち中でスクロール中でない
        cursor_count = msg_dq.current_page.draw_count - msg_dq.current_page.length
        if cursor_count//7 % 2 == 0:
            draw_msg_cursor(msg_dq, 0, (scroll_line_num-1)*line_height-4)


def ui_init(xmlui:XMLUI):
    common_win = win.Decorator(xmlui)
    common_text = text.Decorator(xmlui)

    # 工事中表示用
    # *****************************************************************************
    # ポップアップウインドウ
    # ---------------------------------------------------------
    @common_win.rect_frame("popup_win")  # アニメはしない
    def popup_win(win:win.RectFrame, event:XUEvent):
        pyxel.rect(win.area.x, win.area.y, win.area.w, win.area.h, 0)
        win.draw_frame(pyxel.screen.data_ptr(), [0,7,13], win.area.inflate(-2, -2))

    @common_text.msg("popup_text")
    def popup_text(popup_text:text.Msg, event:XUEvent):
        if XUEvent.Key.BTN_A in event.trg or XUEvent.Key.BTN_B in event.trg:
            popup_text.close()

        # テキスト描画
        area = popup_text.area  # areaは重いので必ずキャッシュ
        h = len(popup_text.text.split()) * system_font.size

        for i,page in enumerate(popup_text.text.split()):
            area = popup_text.area
            x, y = area.aligned_pos(system_font.text_width(page), h, XURect.Align.CENTER, XURect.Align.CENTER)
            pyxel.text(x, y + i*system_font.size, page, 7, system_font.font)


    # ゲーム内共通
    # *****************************************************************************
    # 角丸ウインドウ
    # ---------------------------------------------------------
    # openで値をセットをした後closeされる、closingなのに値はopningになっちゃうので別々に保存する
    CLOSING_CLIP_SIZE="_xmlui_closing_clip_size"
    OPENING_CLIP_SIZE="_xmlui_opening_clip_size"

    @common_win.round_frame("round_win")
    def round_win(round_win:win.RoundFrame, event:XUEvent):
        area = round_win.area
        clip = get_world_clip(round_win).to_offset()  # クリップエリアの設定

        # 表示領域が無ければ完了なので閉じる
        if round_win.is_closing and clip.is_empty:
            round_win.close()  # 即座にclose
            return
        
        # 背景
        pyxel.rect(area.x, area.y, area.w, min(area.h, clip.h+2), 0)

        col = get_text_color()
        shadow_col = get_shadow_color()

        # フレーム
        round_win.draw_frame(pyxel.screen.data_ptr(), [col, shadow_col], area.inflate(-2, -2), clip)

    # ステータスウインドウ( ｰ`дｰ´)ｷﾘｯ
    # ---------------------------------------------------------
    # ステータス各種アイテム
    @common_text.label("status_item")
    def status_item(status_item:text.Label, event:XUEvent):
        # 値の取得
        text = XUTextUtil.format_zenkaku(XUTextUtil.format_dict(status_item.text, user_data.data))

        col = get_text_color()

        # テキストは右寄せ
        area = status_item.area
        x, y = XURect.align_offset(area.w, area.h, system_font.text_width(text) + 5, 0, status_item.align, status_item.valign)
        if area.y+y < get_world_clip(XUWinBase.find_parent_win(status_item)).bottom():
            pyxel.text(area.x + x, area.y + y, text, col, system_font.font)

    # ステータスタイトル(名前)
    @common_text.label("status_title")
    def status_title(status_title:text.Label, event:XUEvent):
        clip = get_world_clip(XUWinBase.find_parent_win(status_title)).intersect(status_title.area)
        pyxel.rect(status_title.area.x, status_title.area.y, status_title.area.w, clip.h, 0)  # タイトルの下地

        col = get_text_color()

        # テキストは左寄せ
        if status_title.area.y < clip.bottom():  # world座標で比較
            x, y = status_title.aligned_pos(system_font)
            pyxel.text(x+1, y-1, user_data.data["name"], col, system_font.font)
