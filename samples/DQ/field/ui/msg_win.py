from xmlui.core import XMLUI,XUEvent,XUWinBase
from msg_dq import Decorator as DQDecorator
from msg_dq import MsgDQ
from ui_common import common_msg_text

def ui_init(xmlui:XMLUI):
    field_dq = DQDecorator(xmlui)

    # フィールド画面のメッセージウインドウ
    # ---------------------------------------------------------
    @field_dq.msg_dq("msg_text")
    def msg_text(msg_text:MsgDQ, event:XUEvent):
        # メッセージ共通処理
        common_msg_text(msg_text, event, True)

        # 自分が閉じたらメニューごと閉じる
        if XUWinBase.find_parent_win(msg_text).win_state == XUWinBase.STATE_CLOSED:
            XUWinBase(msg_text.xmlui.find_by_id("menu")).start_close()

        # 入力アクション
        # ---------------------------------------------------------
        if XUEvent.Key.BTN_A in event.trg or XUEvent.Key.BTN_B in event.now:
            if msg_text.is_all_finish:
                XUWinBase.find_parent_win(msg_text).start_close()  # 閉じる
                return

        if XUEvent.Key.BTN_A in event.trg or XUEvent.Key.BTN_B in event.now:
            if msg_text.is_next_wait:
                msg_text.set_page_no(msg_text.current_page_no+1)  # 次ページへ
                return
