from xmlui.core import XMLUI,XUEvent,XUWinSet

import msg_dq
from msg_dq import MsgDQ

def ui_init(xmlui:XMLUI):
    field_dq = msg_dq.Decorator(xmlui)

    # フィールド画面のメッセージウインドウ
    # ---------------------------------------------------------
    @field_dq.msg_dq("msg_text")
    def msg_text(msg_text:MsgDQ, event:XUEvent):
        # メッセージ共通処理
        msg_text.draw(event, True)

        # 自分が閉じたらメニューごと閉じる
        if XUWinSet.find_parent_win(msg_text).win_state == XUWinSet.WIN_STATE.CLOSED:
            XUWinSet(msg_text.xmlui.find_by_id("menu")).start_close()

        # 入力アクション
        # ---------------------------------------------------------
        if XUEvent.Key.BTN_A in event.trg or XUEvent.Key.BTN_B in event.now:
            if msg_text.is_all_finish:
                XUWinSet.find_parent_win(msg_text).start_close()  # 閉じる
                return

        if XUEvent.Key.BTN_A in event.trg or XUEvent.Key.BTN_B in event.now:
            if msg_text.is_next_wait:
                msg_text.page_no += 1  # 次ページへ
                return
