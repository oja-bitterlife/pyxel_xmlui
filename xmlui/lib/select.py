from typing import Callable
from xmlui.core import XMLUI,XUElem,XUEventItem,XUEvent,_XUSelectBase

# グリッド選択
# *****************************************************************************
class XUGrid(_XUSelectBase):
    ROWS_ATTR = 'rows'
    ITEM_W_ATTR = 'item_w'
    ITEM_H_ATTR = 'item_h'

    def __init__(self, elem:XUElem, init_item_tag:str):
        rows = elem.attr_int(self.ROWS_ATTR, 1)
        item_w = elem.attr_int(self.ITEM_W_ATTR, 0)
        item_h = elem.attr_int(self.ITEM_H_ATTR, 0)
        super().__init__(elem, init_item_tag, rows, item_w, item_h)

    # 入力に応じた挙動一括。変更があった場合はTrue
    def _select_by_event(self, input:set[XUEventItem], left_event:XUEventItem, right_event:XUEventItem, up_event:XUEventItem, down_event:XUEventItem, x_wrap:bool, y_wrap:bool) -> bool:
        old_no = self.selected_no

        if left_event in input:
            self.next(-1, 0, x_wrap, y_wrap)
        elif right_event in input:
            self.next(1, 0, x_wrap, y_wrap)
        elif up_event in input:
            self.next(0, -1, x_wrap, y_wrap)
        elif down_event in input:
            self.next(0, 1, x_wrap, y_wrap)

        return self.selected_no != old_no

    # 選択一括処理Wrap版
    def select_by_event(self, input:set[XUEventItem], left_event:XUEventItem, right_event:XUEventItem, up_event:XUEventItem, down_event:XUEventItem) -> bool:
        return self._select_by_event(input, left_event, right_event, up_event, down_event, True, True)

    # 選択一括処理NoWrap版
    def select_no_wrap(self, input:set[XUEventItem], left_event:XUEventItem, right_event:XUEventItem, up_event:XUEventItem, down_event:XUEventItem) -> bool:
        return self._select_by_event(input, left_event, right_event, up_event, down_event, False, False)


# リスト選択
# *****************************************************************************
class _XUListBase(_XUSelectBase):
    def __init__(self, elem:XUElem, item_tag:str, rows:int, item_w:int, item_h:int, next_move=[0, 0]):
        super().__init__(elem, item_tag, rows, item_w, item_h)
        self.next_move = next_move

    # 入力に応じた挙動一括。変更があった場合はTrue
    def _select_by_event(self, input:set[XUEventItem], prev_event:XUEventItem, next_event:XUEventItem, wrap:bool) -> bool:
        old_no = self.selected_no

        if prev_event in input:
            self.next(-self.next_move[0], -self.next_move[1], wrap, wrap)
        elif next_event in input:
            self.next(self.next_move[0], self.next_move[1], wrap, wrap)

        return self.selected_no != old_no

    # 選択一括処理Wrap版
    def select_by_event(self, input:set[XUEventItem], prev_event:XUEventItem, next_event:XUEventItem) -> bool:
        return self._select_by_event(input, prev_event, next_event, True)

    # 選択一括処理NoWrap版
    def select_no_wrap(self, input:set[XUEventItem], prev_event:XUEventItem, next_event:XUEventItem) -> bool:
        return self._select_by_event(input, prev_event, next_event, False)

# 縦方向リスト
# ---------------------------------------------------------
class XUList(_XUListBase):
    ITEM_H_ATTR = 'item_h'

    def __init__(self, elem:XUElem, init_item_tag:str):
        item_h = elem.attr_int(self.ITEM_H_ATTR, 0)
        super().__init__(elem, init_item_tag, 1, 0, item_h, [0, 1])

# 横方向リスト
# ---------------------------------------------------------
class XURowList(_XUListBase):
    ITEM_W_ATTR = 'item_w'

    def __init__(self, elem:XUElem, init_item_tag:str):
        rows = len(elem.find_by_tagall(init_item_tag))
        item_w = elem.attr_int(self.ITEM_W_ATTR, 0)
        super().__init__(elem, init_item_tag, rows, item_w, 0, [1, 0])


# デコレータを用意
# *****************************************************************************
class Decorator(XMLUI.HasRef):
    def grid(self, tag_name:str, init_item_tag:str):
        def wrapper(bind_func:Callable[[XUGrid,XUEvent], str|None]):
            # 登録用関数をジェネレート
            def draw(elem:XUElem, event:XUEvent):
                return bind_func(XUGrid(elem, init_item_tag), event)
            # 関数登録
            self.xmlui.set_drawfunc(tag_name, draw)
        return wrapper

    def list(self, tag_name:str, init_item_tag:str):
        def wrapper(bind_func:Callable[[XUList,XUEvent], str|None]):
            # 登録用関数をジェネレート
            def draw(elem:XUElem, event:XUEvent):
                return bind_func(XUList(elem, init_item_tag), event)
            # 関数登録
            self.xmlui.set_drawfunc(tag_name, draw)
        return wrapper

    def row_list(self, tag_name:str, init_item_tag:str):
        def wrapper(bind_func:Callable[[XURowList,XUEvent], str|None]):
            # 登録用関数をジェネレート
            def draw(elem:XUElem, event:XUEvent):
                return bind_func(XURowList(elem, init_item_tag), event)
            # 関数登録
            self.xmlui.set_drawfunc(tag_name, draw)
        return wrapper

