import xmlui_core as xuc

# パッケージ一覧
from . import input
from . import text
from . import win


# XMLUIのおすすめ設定による初期化をよしなにやってくれるやつ
# これを呼ぶだけでだいたいいい感じになるように頑張る
def xmlui_pyxel_init(
        xmlui:xuc.XMLUI,
        inputlist_dict: dict[str,list[int]],
        font_path:str
    ):
    input.set_Inputlist_fromdict(xmlui, inputlist_dict)

    text.default = text.Font(font_path)

