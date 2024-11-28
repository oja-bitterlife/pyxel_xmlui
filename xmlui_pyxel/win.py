import pyxel

from xmlui_core import *
from . import xui

# ウインドウ基底
# *****************************************************************************
_WINDOW_SPEED = 16

# アクティブカラーにする
def _active_color(state:XUStateRO, color:int):
        return 10 if  state.xmlui.debug and state.xmlui.active_state == state and color == 7 else color

class _BaseRound(XUWinRound):
    DEFAULT_PAT = [7,7,12]

    def __init__(self, state:XUStateRO):
        pat = [_active_color(state, c)  for c in self.DEFAULT_PAT]  # アクティブカラーに
        super().__init__(state, pat, pyxel.width, pyxel.height)

    def draw(self):
        self.clip.h = self.update_count*_WINDOW_SPEED
        self.draw_buf(pyxel.screen.data_ptr())

class _BaseRect(XUWinRect):
    DEFAULT_PAT = [7,7,12]

    def __init__(self, state:XUStateRO):
        pat = [_active_color(state, c)  for c in self.DEFAULT_PAT]  # アクティブカラーに
        super().__init__(state, pat, pyxel.width, pyxel.height)

    def draw(self):
        self.clip.h = self.update_count*_WINDOW_SPEED
        self.draw_buf(pyxel.screen.data_ptr())


# グリッドメニュー付きウインドウ
# *****************************************************************************
class MenuRO(_BaseRound):
    def __init__(self, state:XUStateRO, tag_group:str, tag_item:str):
        super().__init__(state)
        self._grid_root = XUSelectGrid(state, tag_group, tag_item)

    def draw(self):
        super().draw()
        for group in self._grid_root._grid:
            for item in group:
                if self.clip.h >= item.area.y-self.area.y + xui.FONT_SIZE:  # ウインドウが表示されるまで表示しない
                    pyxel.text(item.area.x+6, item.area.y, item.text, 7, xui.font)

    @property
    def selected_item(self) -> XUStateRO:
        return self._grid_root.selected_item

class Menu(MenuRO):
    def __init__(self, state:XUState, tag_group:str, tag_item:str):
        super().__init__(state, tag_group, tag_item)

    def arrange_items(self, w:int, h:int):
        self._grid_root.arrange_items(w, h)

    def select_by_event(self, left:str, right:str, up:str, down:str) -> XUState:
        if self.xmlui.active_state == self:
            self._grid_root.select_by_event(self.xmlui._event.trg, left, right, up, down)
        return self.selected_item

    @property
    def selected_item(self) -> XUState:
        return self._grid_root.selected_item


# デコレータを用意
def menu_update_bind(xmlui:XMLUI, tag_name:str, tag_group:str, tag_item:str):
    def wrapper(update_func:Callable[[Menu,XUEvent], None]):
        # 登録用関数をジェネレート
        def update(state:XUState, event:XUEvent):
            update_func(Menu(state, tag_group, tag_item), event)
        # 関数登録
        xmlui.set_updatefunc(tag_name, update)
    return wrapper

def menu_draw_bind(xmlui:XMLUI, tag_name:str, tag_group:str, tag_item:str):
    def wrapper(draw_func:Callable[[MenuRO,XUEvent], None]):
        # 登録用関数をジェネレート
        def draw(state:XUStateRO, event:XUEvent):
            draw_func(MenuRO(state, tag_group, tag_item), event)
        # 関数登録
        xmlui.set_drawfunc(tag_name, draw)
    return wrapper


# リストウインドウ
# *****************************************************************************
class ListRO(_BaseRound):
    def __init__(self, state:XUStateRO, tag_item:str):
        super().__init__(state)
        self._grid_root = XUSelectList(state, tag_item)

    def draw(self):
        super().draw()
        for group in self._grid_root._grid:
            item = group[0]
            if self.clip.h >= item.area.y-self.area.y + xui.FONT_SIZE:  # ウインドウが表示されるまで表示しない
                pyxel.text(item.area.x+6, item.area.y, item.text, 7, xui.font)

    @property
    def selected_item(self) -> XUStateRO:
        return self._grid_root.selected_item

class List(ListRO):
    def __init__(self, state:XUState, tag_item:str):
        super().__init__(state, tag_item)

    def arrange_items(self, w:int, h:int):
        self._grid_root.arrange_items(w, h)

    def select_by_event(self, up:str, down:str) -> XUState:
        if self.xmlui.active_state == self:
            self._grid_root.select_by_event(self.xmlui._event.trg, up, down)
        return self.selected_item

    @property
    def selected_item(self) -> XUState:
        return self._grid_root.selected_item


# デコレータを用意
def list_update_bind(xmlui:XMLUI, tag_name:str, tag_item:str):
    def wrapper(update_func:Callable[[List,XUEvent], None]):
        # 登録用関数をジェネレート
        def update(state:XUState, event:XUEvent):
            update_func(List(state, tag_item), event)
        # 関数登録
        xmlui.set_updatefunc(tag_name, update)
    return wrapper

def list_draw_bind(xmlui:XMLUI, tag_name:str, tag_item:str):
    def wrapper(draw_func:Callable[[ListRO,XUEvent], None]):
        # 登録用関数をジェネレート
        def draw(state:XUStateRO, event:XUEvent):
            draw_func(ListRO(state, tag_item), event)
        # 関数登録
        xmlui.set_drawfunc(tag_name, draw)
    return wrapper


# メッセージウインドウ
# *****************************************************************************
class MsgRO(_BaseRound):
    LINE_NUM_ATTR = "lines"
    WRAP_ATTR = "wrap"
    SPEED_ATTR = "speed"

    def __init__(self, state:XUStateRO, tag_text:str):
        super().__init__(state)

        self._page_root = state.find_by_tag(tag_text)
        self.page = XUPageRO(self._page_root)

    def draw(self):
        super().draw()
        for i,page in enumerate(self.page.page_text.split()):
            # 子を強制描画するのでvaliedチェック
            if self.page.state.valid > 0:
                area = self.page.state.area
                pyxel.text(area.x, area.y+i*xui.FONT_SIZE, page, 7, xui.font)

class Msg(MsgRO):
    def __init__(self, state:XUState, tag_text:str):
        # PAGEがなければ新規作成。あればそれを使う
        self._page_root = state.find_by_tag(tag_text)
        page = XUPage(self._page_root, self._page_root.text, self._page_root.attr_int(self.LINE_NUM_ATTR, 1), self._page_root.attr_int(self.WRAP_ATTR))

        super().__init__(state, tag_text)

        # 親でself.pageが上書きされるので、あとからself.pageに突っ込む
        self.page = page.nextcount(self._page_root.attr_float(self.SPEED_ATTR, 1))

    def set_speed(self, speed:float):
        self._page_root.set_attr(self.SPEED_ATTR, speed)


# デコレータを用意
def msg_update_bind(xmlui:XMLUI, tag_name:str, tag_text:str):
    def wrapper(update_func:Callable[[Msg,XUEvent], None]):
        # 登録用関数をジェネレート
        def update(state:XUState, event:XUEvent):
            update_func(Msg(state, tag_text), event)
        # 関数登録
        xmlui.set_updatefunc(tag_name, update)
    return wrapper

def msg_draw_bind(xmlui:XMLUI, tag_name:str, tag_text:str):
    def wrapper(draw_func:Callable[[MsgRO,XUEvent], None]):
        # 登録用関数をジェネレート
        def draw(state:XUStateRO, event:XUEvent):
            draw_func(MsgRO(state, tag_text), event)
        # 関数登録
        xmlui.set_drawfunc(tag_name, draw)
    return wrapper
