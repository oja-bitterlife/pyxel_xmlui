import pyxel

from xmlui.core import XURect,XUEvent,XUWinInfo
from xmlui.lib import win,text,debug

from system import system_font,system_palette


# 共通定義
# *****************************************************************************
WIN_OPEN_SPEED   = 16
WIN_CLOSE_SPEED   = 32
KOJICHU_COL = 15

FRAME_OUT = system_palette.pal_gray16[3]
FRAME_COL = 7
FRAME_SHADOW_COL = system_palette.pal_gray16[5]
FRAME_BG_COL = system_palette.pal_colors[40]

# 共通で使える関数
def get_world_clip(win:XUWinInfo) -> XURect:
    area = win.area
    if win.is_opening:
        clip_size = min(int(win.opening_count * WIN_OPEN_SPEED), area.h)
        area.h = clip_size
    else:
        clip_size = max(int(win.closing_count * WIN_CLOSE_SPEED), 0)
        area.h -= clip_size
    return area


# ui初期化
# *****************************************************************************
def ui_init(xmlui:debug.DebugXMLUI):
    common_win = win.Decorator(xmlui)
    common_text = text.Decorator(xmlui)

    # 工事中表示用
    # *****************************************************************************
    # ポップアップウインドウ
    # ---------------------------------------------------------
    @common_win.rect_frame("popup_win")  # アニメはしない
    def popup_win(win:win.XURectFrame, event:XUEvent):
        pyxel.rect(win.area.x, win.area.y, win.area.w, win.area.h, 0)
        win.draw_frame(pyxel.screen.data_ptr(), [0,7,13], win.area.inflate(-2, -2))

    @common_text.msg("popup_text")
    def popup_text(popup_text:text.XUMsg, event:XUEvent):
        if event.check_trg(XUEvent.Key.BTN_A, XUEvent.Key.BTN_B):
            win = XUWinInfo.find_parent_win(popup_text)
            XUWinInfo.find_parent_win(popup_text).close()

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
    @common_win.round_frame("round_win")
    def round_win(round_win:win.XURoundFrame, event:XUEvent):
        area = round_win.area
        clip = get_world_clip(round_win).to_offset()  # クリップエリアの設定

        # 表示領域が無ければ完了なので閉じる
        if round_win.is_closing and clip.is_empty:
            # 子の終了待ち
            if not round_win.find_child_win():
                round_win.finish()  # 完了
        
        # 背景
        pyxel.rect(area.x, area.y, area.w, min(area.h, clip.h+1), 0)
        inside_area = area.inflate(-2, -2)
        pyxel.rect(inside_area.x, inside_area.y, inside_area.w, min(inside_area.h, clip.h-1), FRAME_BG_COL)

        # フレーム
        round_win.draw_frame(pyxel.screen.data_ptr(), [FRAME_OUT, FRAME_COL, FRAME_SHADOW_COL, FRAME_SHADOW_COL], area.inflate(-1, -1), clip)
