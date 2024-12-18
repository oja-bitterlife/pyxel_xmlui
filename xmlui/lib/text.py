from xmlui.core import *
from xmlui.core import XUPageItem

# フォントを扱う
# #############################################################################
class FontBase:
    def __init__(self, font:Any, size:int):
        self.font = font
        self.size = size

    # フォントサイズ算出
    @classmethod
    def get_bdf_size(cls, bdf_font_path):
        with open(bdf_font_path, "r") as f:
            for i, line in enumerate(f.readlines()):
                if i > 100:  # 100行も見りゃええじゃろ...
                    raise Exception(f"{bdf_font_path} has not PIXEL_SIZE")
                if line.startswith("PIXEL_SIZE"):
                    return int(line.split()[-1])
        raise Exception(f"{bdf_font_path} has not PIXEL_SIZE")

    def text_width(self, text:str) -> int:
        return len(text) * self.size

    def text_height(self, text:str) -> int:
        return len(text.splitlines()) * self.size


# テキストを扱う
# #############################################################################
# ラベル
class Label(XUElem):
    ALIGN_ATTR = 'align'  # horizonアライメント
    VALIGN_ATTR = 'valign'  # verticalアライメント

    def __init__(self, elem:XUElem):
        super().__init__(elem.xmlui, elem._element)
        self.align = elem.attr_str(self.ALIGN_ATTR, XURect.ALIGN_LEFT)
        self.valign = elem.attr_str(self.VALIGN_ATTR, XURect.ALIGN_TOP)

    def aligned_pos(self, font:FontBase) -> tuple[int, int]:
        area = self.area
        return area.aligned_pos(font.text_width(self.text), font.size, self.align, self.valign)

# メッセージ(ページつきアニメテキスト)
class Msg(XUPageText):
    PAGE_LINE_NUM_ATTR = 'page_line_num'  # 1ページに含まれる行数
    WRAP_ATTR = 'wrap'  # 1行の最大長(折り返し位置)

    # タグのテキストを処理する
    def __init__(self, elem:XUElem):
        # パラメータはXMLから取得
        page_line_num = elem.attr_int(self.PAGE_LINE_NUM_ATTR, 1024)
        wrap = elem.attr_int(self.WRAP_ATTR, 4096)

        super().__init__(elem, page_line_num, wrap)

    # 全角にして登録
    def append_msg(self, text:str, all_params:dict[str,Any]={}) -> list[XUPageItem]:
        return self.add_pages(XUTextUtil.format_zenkaku(text, all_params), self.page_line_num, self.wrap)


# デコレータを用意
# *****************************************************************************
class Decorator(XUTemplate.HasRef):
    def label(self, tag_name:str):
        def wrapper(bind_func:Callable[[Label,XUEvent], str|None]):
            # 登録用関数をジェネレート
            def draw(elem:XUElem, event:XUEvent):
                return bind_func(Label(elem), event)
            # 関数登録
            self.template.set_drawfunc(tag_name, draw)
        return wrapper

    def msg(self, tag_name:str):
        def wrapper(bind_func:Callable[[Msg,XUEvent], str|None]):
            # 登録用関数をジェネレート
            def draw(elem:XUElem, event:XUEvent):
                return bind_func(Msg(elem), event)
            # 関数登録
            self.template.set_drawfunc(tag_name, draw)
        return wrapper
