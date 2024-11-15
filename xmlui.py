import xml.etree.ElementTree
from xml.etree.ElementTree import Element
from typing import Callable,Any

import re

# 描画領域計算用
class UI_RECT:
    def __init__(self, x:int, y:int, w:int, h:int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def intersect(self, other):
        right = min(self.x+self.w, other.x+other.w)
        left = max(self.x, other.x)
        bottom = min(self.y+self.h, other.y+other.h)
        top = max(self.y, other.y)
        return UI_RECT(left, top, right-left, bottom-top)
    
    def contains(self, x, y):
        return self.x <= x < self.x+self.w and self.y <= y < self.y+self.h

    def __repr__(self) -> str:
        return f"RECT({self.x}, {self.y}, {self.w}, {self.h})"


# UIパーツの状態保存用
class UI_STATE:
    # プロパティ定義
    # 一度しか初期化されないので定義と同時に配列等オブジェクトを代入すると事故る
    # のでconstructorで初期化する
    # XML構造
    element: Element  # 自身のElement
    parent: 'UI_STATE'  # 親Element

    # 表示関係
    area: UI_RECT  # 描画範囲
    hide: bool  # 非表示フラグ

    # 制御関係
    update_count: int  # 更新カウンター
    remove: bool  # 削除フラグ
    append_list: list['UI_STATE']  # 追加リスト

    def __init__(self, element: Element):
        # プロパティの初期化
        self.element = element
        self.area = UI_RECT(0, 0, 4096, 4096)
        self.hide = False
        self.update_count = 0
        self.remove = False
        self.append_list = []

        # ステート取得
        if "id" in self.element.attrib:
            self.id = self.element.attrib["id"]
        self.hide = self.attrBool("hide", False)

    # attribアクセス用
    def attrInt(self, key: str, default: int) -> int:
        return int(self.element.attrib.get(key, default))

    def attrStr(self, key: str, default: str) -> str:
        return self.element.attrib.get(key, default)

    def attrBool(self, key: str, default: bool) -> bool:
        attr = self.element.attrib.get(key)
        return default if attr == None else (True if attr.lower() == "true"else False)

    def getText(self) -> str:
        return self.element.text.strip() if self.element.text != None else ""

    def hasAttr(self, key: str) -> bool:
        return key in self.element.attrib

    def setAttr(self, key: str, value: str):
        self.element.attrib[key] = value

    # ツリー操作用
    def addChild(self, state:'UI_STATE'):
        self.append_list.append(state)

    def makeElement(self, name:str, attr:dict[str,str]={}) -> 'UI_STATE':
        return UI_STATE(self.element.makeelement(name, attr))

    def duplicate(self) -> 'UI_STATE':
        return UI_STATE(self.element.makeelement(self.element.tag, self.element.attrib.copy()))


# テキスト表示用
class UI_TEXT:
    src: str  # パラメータ置換済み文字列
    tokens: list[str]  # 行(+wrap)分割済み文字列

    # 改行とwrapで分割する
    def __init__(self, text:str, params:dict[str:Any]={}, wrap:int=1024, sepexp=r"\n|\\n"):
        self.src = text.format(**params)
        self.tokens = []

        # 行分割
        lines = re.split(sepexp, self.src)

        # wrap分割
        for line in lines:
            while(len(line) > wrap):
                self.tokens.append(line[:wrap])
                line = line[wrap:]
            # 残りを保存
            if len(line) > 0:
                self.tokens.append(line[:wrap])

    # 最大文字数に減らして取得
    def get(self, limit:int=65535):
        limit = int(limit)  # 計算式だとfloatが型チェックをスルーする
        out = []

        count = 0
        for token in self.tokens:
            # limitに届いていない間はそのまま保存
            if len(token)+count < limit:
                out.append(token)
                count += len(token)
            # limitを越えそう
            else:
                # limitまで取得
                over = token[:limit-count]
                if len(over) > 0:
                    out.append(over)
                break

        return out

    def __len__(self) -> int:
        return len("".join(self.tokens))

# XMLでUIライブラリ本体
# #############################################################################
class XMLUI:
    root: UI_STATE
    state_map: dict[Element, UI_STATE] = {}  # 状態保存用

    update_funcs: dict[str, Callable[['XMLUI',UI_STATE], None]] = {}
    draw_funcs: dict[str, Callable[['XMLUI',UI_STATE], None]] = {}

    # 初期化
    # *************************************************************************
    # ファイルから読み込み
    @classmethod
    def createFromFile(cls, fileName: str):
        with open(fileName, "r", encoding="utf8") as f:
            return cls.createFromString(f.read())

    # リソースから読み込み
    @classmethod
    def createFromString(cls, xml_data: str):
            return XMLUI(xml.etree.ElementTree.fromstring(xml_data))

    # 初期化。<xmlui>を持つXMLを突っ込む
    def __init__(self, dom: xml.etree.ElementTree.Element):
        # 最上位がxmluiでなくてもいい
        if dom.tag == "xmlui":
            xmlui_root = dom
        else:
            # 最上位でないときは子から探す
            xmlui_root = dom.find("xmlui")
            # 見つからなかったら未対応のXML
            if xmlui_root is None:
                raise Exception("<xmlui> not found")

        # state_mapの作成
        self.state_map = XMLUI._makeState(xmlui_root, {})

        # rootを取り出しておく
        self.root = self.state_map[xmlui_root]


    # XML操作用
    # *************************************************************************
    def findByID(self, id: str, root:UI_STATE|None=None) -> UI_STATE|None:
        rootElement = root.element if root != None else self.root.element
        for element in rootElement.iter():
            if element.attrib.get("id") == id:
                return self.state_map[element]
        return None

    def findByTag(self, tag: str, root:UI_STATE|None=None) -> UI_STATE|None:
        rootElement = root.element if root != None else self.root.element
        for element in rootElement.iter():
            if element.tag == tag:
                return self.state_map[element]
        return None


    # 更新用
    # *************************************************************************
    # 全体を呼び出す処理
    def update(self):
        # 各ノードのUpdate
        for element in self.root.element.iter():
            state = self.state_map[element]

            # 更新処理
            self.updateElement(element.tag, state)
            state.update_count += 1  # 実行後に更新

        # ノードの追加と削除
        for state in self.state_map.values():
            # removeがマークされたノードは削除
            if state.remove and state != self.root:
                state.parent.element.remove(state.element)

            # appendされたノードを追加
            for child in state.append_list:
                state.element.append(child.element)
            state.append_list = []

        # Treeが変更されたかもなのでstateを更新
        self.state_map = XMLUI._makeState(self.root.element, self.state_map)

    # stateの更新
    @classmethod
    def _makeState(cls, root_element: Element, old_map: dict[Element,UI_STATE]) -> dict[Element,UI_STATE]:
        # state_mapの更新
        state_map = {element: old_map.get(element, UI_STATE(element)) for element in root_element.iter()}

        # state_mapのparentを更新
        def _updateStateParentRec(parent: Element):
            for child in parent:
                state_map[child].parent = state_map[parent]
                _updateStateParentRec(child)
        _updateStateParentRec(root_element)

        return state_map


    # 描画用
    # *************************************************************************
    def draw(self):
        # ツリーの描画
        self._drawTreeRec(self.root.element)

    # ツリーのノード以下を再帰処理
    def _drawTreeRec(self, parent: Element):
        state = self.state_map[parent]

        # 非表示なら子も含めて描画しない
        if state.hide:
            return

        # 親を先に描画する(子を上に描画)
        if state != self.root:  # rootは親を持たないので更新不要
            state.area = XMLUI._updateArea(state)  # エリア更新
        self.drawElement(parent.tag, state)

        # 子の処理
        for node in parent:
            self._drawTreeRec(node)

    # 子のエリア設定(親のエリア内に収まるように)
    @classmethod
    def _updateArea(cls, state:UI_STATE) -> UI_RECT:
        element = state.element

        # 親からのオフセットで計算
        _x = int(element.attrib.get("x", 0))
        _y = int(element.attrib.get("y", 0))
        w = int(element.attrib.get("w", state.parent.area.w))
        h = int(element.attrib.get("h", state.parent.area.h))

        # paddingも設定できるように
        _x += sum([int(element.attrib.get(name, 0)) for name in ["padding_x", "padding_l", "padding_size"]])
        w -= sum([int(element.attrib.get(name, 0)) for name in ["padding_x", "padding_size"]])*2
        _y += sum([int(element.attrib.get(name, 0)) for name in ["padding_y", "padding_t", "padding_size"]])
        h -= sum([int(element.attrib.get(name, 0)) for name in ["padding_y", "padding_size"]])*2
        w -= sum([int(element.attrib.get(name, 0)) for name in ["padding_l", "padding_r"]])
        h -= sum([int(element.attrib.get(name, 0)) for name in ["padding_t", "padding_b"]])

        # 親の中だけ表示するようにintersect
        return UI_RECT(state.parent.area.x+_x, state.parent.area.y+_y, w, h).intersect(state.parent.area)


    # 個別処理。関数のオーバーライドでもいいし、個別関数登録でもいい
    def updateElement(self, name: str, state: UI_STATE):
        # 登録済みの関数だけ実行
        if name in self.update_funcs:
            self.update_funcs[name](self, state)

    def drawElement(self, name: str, state: UI_STATE):
        # 登録済みの関数だけ実行
        if name in self.draw_funcs:
            self.draw_funcs[name](self, state)

    # 個別処理登録
    def setUpdateFunc(self, name: str, func: Callable[['XMLUI',UI_STATE], None]):
        self.update_funcs[name] = func

    def setDrawFunc(self, name: str, func: Callable[['XMLUI',UI_STATE], None]):
        self.draw_funcs[name] = func

