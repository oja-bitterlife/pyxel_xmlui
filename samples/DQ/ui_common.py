import pyxel

# xmlui_pyxelの初期化
# *****************************************************************************
from xmlui.core import XMLUI,XUDebug,XUElem,XUEvent,XUWinBase,XURect,XUTextUtil
from xmlui.lib import text,win
from xmlui_modules import dq

from xmlui.ext.pyxel_util import PyxelFont,PyxelPalette
import db

system_font = PyxelFont("assets/font/b12.bdf")
system_palette = PyxelPalette()

# ライブラリのインスタンス化
xmlui = XMLUI(pyxel.width, pyxel.height, XUDebug.DEBUGLEVEL_LIB)
common_template = xmlui.load_template("assets/ui/common.xml")


# 共通定義
# *****************************************************************************
WIN_OPEN_SPEED   = 16
WIN_CLOSE_SPEED   = 32
KOJICHU_COL = 15


# 共通で使える関数
# *****************************************************************************
# カーソル描画
def draw_menu_cursor(state:XUElem, x:int, y:int):
    tri_size = 6
    left = state.area.x + x
    top = state.area.y+2 + y
    pyxel.tri(left, top, left, top+tri_size, left+tri_size//2, top+tri_size//2, 7)

def draw_msg_cursor(state:XUElem, x:int, y:int):
    tri_size = 6
    center_x = 127-tri_size//2+x  # Xはど真ん中固定で
    y = state.area.y + tri_size - 3 + y
    pyxel.tri(center_x, y, center_x+tri_size, y, center_x+tri_size//2, y+tri_size//2, 7)

def get_world_clip(win:XUWinBase) -> XURect:
    area = win.area
    if win.is_opening:
        clip_size = min(int(win.opening_count * WIN_OPEN_SPEED), area.h)
        area.h = clip_size
    else:
        clip_size = max(int(win.closing_count * WIN_CLOSE_SPEED), 0)
        area.h -= clip_size
    return area

common_win = win.Decorator(common_template)
common_text = text.Decorator(common_template)

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
        x, y = area.aligned_pos(system_font.text_width(page), h, XURect.ALIGN_CENTER, XURect.ALIGN_CENTER)
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
    
    # 背景
    pyxel.rect(area.x, area.y, area.w, min(area.h, clip.h+2), 0)

    # フレーム
    round_win.draw_frame(pyxel.screen.data_ptr(), [7, 13], area.inflate(-2, -2), clip)

# メッセージウインドウ
# ---------------------------------------------------------
def common_msg_text(msg_dq:dq.MsgDQ, event:XUEvent, cursor_visible:bool):
    area = msg_dq.area  # areaは重いので必ずキャッシュ

    # テキスト表示
    # ---------------------------------------------------------
    msg_dq.current_page.draw_count += 0.5

    # スクロール表示
    # ---------------------------------------------------------
    # スクロールバッファサイズはページサイズ+2(待機中は+1)
    idle_scroll_size = msg_dq.attr_int(msg_dq.PAGE_LINE_NUM_ATTR) + 1
    anim_scroll_size = msg_dq.attr_int(msg_dq.PAGE_LINE_NUM_ATTR) + 2
    scroll_size = idle_scroll_size if msg_dq.current_page.is_finish else anim_scroll_size
    scroll_info =  msg_dq.get_scroll_lines(scroll_size)

    # アニメーション用表示位置ずらし。スクロール時半文字ずれる
    shift_y = -3 if not msg_dq.current_page.is_finish and len(scroll_info) >= anim_scroll_size else 5

    # テキスト描画
    line_height = system_font.size + 3  # 行間設定
    for i,info in enumerate(scroll_info):
        # xはインデント
        x = area.x
        if info.mark_type == dq.MsgDQ.Mark.TALK:
            x += system_font.text_width(dq.MsgDQ.TALK_START)
        elif info.mark_type == dq.MsgDQ.Mark.ENEMY:
            x += system_font.size

        # yはスクロール
        y = shift_y + area.y + i*line_height

        pyxel.text(x, y, info.line_text, 7, system_font.font)

    # カーソル表示
    # ---------------------------------------------------------
    if cursor_visible and msg_dq.is_next_wait:
        cursor_count = msg_dq.current_page.draw_count - msg_dq.current_page.length
        if cursor_count//7 % 2 == 0:
            draw_msg_cursor(msg_dq, 0, scroll_size*line_height + shift_y-3)

    # 表示途中のアクション
    if not msg_dq.is_next_wait:
        if XUEvent.Key.BTN_A in event.now or XUEvent.Key.BTN_B in event.now:
            msg_dq.current_page.draw_count += 2  # 素早く表示


# ステータスウインドウ( ｰ`дｰ´)ｷﾘｯ
# ---------------------------------------------------------
# ステータス各種アイテム
@common_text.label("status_item")
def status_item(status_item:text.Label, event:XUEvent):
    # 値の取得
    text = XUTextUtil.format_zenkaku(XUTextUtil.format_dict(status_item.text, vars(db.user_data)))

    # テキストは右寄せ
    area = status_item.area
    x, y = XURect.align_offset(area.w, area.h, system_font.text_width(text) + 5, 0, status_item.align, status_item.valign)
    if area.y+y < get_world_clip(XUWinBase.find_parent_win(status_item)).bottom():
        pyxel.text(area.x + x, area.y + y, text, 7, system_font.font)

# ステータスタイトル(名前)
@common_text.label("status_title")
def status_title(status_title:text.Label, event:XUEvent):
    clip = get_world_clip(XUWinBase.find_parent_win(status_title)).intersect(status_title.area)
    pyxel.rect(status_title.area.x, status_title.area.y, status_title.area.w, clip.h, 0)  # タイトルの下地

    # テキストは左寄せ
    if status_title.area.y < clip.bottom():  # world座標で比較
        x, y = status_title.aligned_pos(system_font)
        pyxel.text(x+1, y-1, db.user_data.name, 7, system_font.font)
