import pyxel

from xmlui.core import XUSelectItem
from ui_common import system_font,draw_menu_cursor,KOJICHU_COL

def menu_item(menu_item:XUSelectItem):
    area = menu_item.area
    col = KOJICHU_COL if menu_item.value == "工事中" else 7
    pyxel.text(area.x+6, area.y, menu_item.text, col, system_font.font)

    # カーソル追加
    if menu_item.selected:
        draw_menu_cursor(menu_item, 0, 1)
