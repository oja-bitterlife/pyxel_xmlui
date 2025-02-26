from xmlui.core import XMLUI,XUEvent,XUEventItem
from xmlui.lib import select

from title.ui.item import menu_item

# タイトル画面UI
# ---------------------------------------------------------
from ui_common import draw_menu_cursor
def ui_init(xmlui:XMLUI):
    title_select = select.Decorator(xmlui)

    # START/CONTINUE選択
    @title_select.list("game_start", "menu_item")
    def game_start(game_start:select.XUList, event:XUEvent):
        # 選択肢描画
        for item in game_start.items:
            menu_item(item)

        # メニュー選択
        game_start.select_by_event(event.trg, *XUEvent.Key.UP_DOWN())
        if event.check_trg(XUEvent.Key.BTN_A):
            # ゲームメインへイベント通知
            game_start.on(game_start.selected_item.action)
