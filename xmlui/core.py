# XMLを使うよ
import xml.etree.ElementTree
from xml.etree.ElementTree import Element

# 型を使うよ
from typing import Callable,Any,Self
from enum import StrEnum

# 日本語対応
import unicodedata

# その他よく使う奴
import re,math
from copy import deepcopy

# 描画領域計算用
# #############################################################################
class XURect:
    class Align(StrEnum):
        CENTER = "center"
        LEFT = "left"
        RIGHT = "right"
        TOP = "top"
        BOTTOM = "bottom"

        @classmethod
        def from_str(cls, type_:str) -> "XURect.Align":
            for v in cls.__members__.values():
                if v == type_:
                    return v
            raise RuntimeError(f"Invalid Align type: {type_}")

    def __init__(self, x:int, y:int, w:int, h:int):
        self.x = x
        self.y = y
        self.w = max(0, w)
        self.h = max(0, h)

    def copy(self) -> "XURect":
        return XURect(self.x, self.y, self.w, self.h)

    # 変換
    def intersect(self, other:"XURect") -> "XURect":
        right = min(self.x+self.w, other.x+other.w)
        left = max(self.x, other.x)
        bottom = min(self.y+self.h, other.y+other.h)
        top = max(self.y, other.y)
        return XURect(left, top, right-left, bottom-top)

    def inflate(self, w, h) -> "XURect":
        return XURect(self.x-w, self.y-h, self.w+w*2, self.h+h*2)

    # offset化
    def to_offset(self) -> "XURect":
        return XURect(0, 0, self.w, self.h)

    # 内包チェック
    def contains_x(self, x:int) -> bool:
        return self.x <= x < self.x+self.w

    def contains_y(self, y:int) -> bool:
        return self.y <= y < self.y+self.h

    def contains(self, x, y) -> bool:
        return self.x <= x < self.x+self.w and self.y <= y < self.y+self.h

    # 空チェック
    @property
    def is_empty(self) -> int:
        return self.w <= 0 or self.h <= 0

    # 座標取得
    def center_x(self, w:int=0) -> int:
        return self.x + (self.w-w)//2

    def center_y(self, h:int=0) -> int:
        return self.y + (self.h-h)//2

    def right(self, right_space:int=0) -> int:
        return self.x + self.w - right_space

    def bottom(self, bottom_space:int=0) -> int:
        return self.y + self.h - bottom_space

    # 座標取得(w,h = content w,h)
    @classmethod
    def align_offset(cls, area_w:int, area_h:int, w:int=0, h:int=0, align:Align=Align.CENTER, valign:Align=Align.CENTER) -> tuple[int, int]:
        area = XURect(0, 0, area_w, area_h)
        match align:
            case cls.Align.LEFT:
                x = 0
            case cls.Align.CENTER:
                x = area.center_x(w)
            case cls.Align.RIGHT:
                x = area.right(w)
            case _:
                raise ValueError(f"align:{align} is not supported.")

        match valign:
            case cls.Align.TOP:
                y = 0
            case cls.Align.CENTER:
                y = area.center_y(h)
            case cls.Align.BOTTOM:
                y = area.bottom(h)
            case _:
                raise ValueError(f"align:{valign} is not supported.")
        return x,y

    def aligned_pos(self, w:int, h:int, align:Align=Align.CENTER, valign:Align=Align.CENTER) -> tuple[int, int]:
        offset_x, offset_y = self.align_offset(self.w, self.h, w, h, align, valign)
        return self.x + offset_x, self.y + offset_y

    def __repr__(self) -> str:
        return f"RECT({self.x}, {self.y}, {self.w}, {self.h})"


# イベント管理用
# #############################################################################
class XUEventItem(str):
    def __new__(cls, val:str):
        return super().__new__(cls, val)

class XUEvent:
    # 綴り間違いをしないようuse_eventをチェックする時は定数を使うようにする
    class UseEvent(StrEnum):
        ABSORBER = "absorber"
        LISTENER = "listener"
        NONE = "none"

    def __init__(self, init_active=False):
        self.is_active = init_active  # アクティブなイベントかどうか
        self.on_init = False
        self.clear()

    def clear(self):
        self._receive:set[XUEventItem] = set([])  # 次の状態受付

        self.now:set[XUEventItem] = set([])
        self.trg:set[XUEventItem] = set([])
        self.release:set[XUEventItem] = set([])

    def clear_trg(self):
        self.trg:set[XUEventItem] = set([])
        self.release:set[XUEventItem] = set([])

    # 更新
    def update(self):
        # 状態更新
        self.trg = set([i for i in self._receive if i not in self.now])
        self.release = set([i for i in self.now if i not in self._receive])
        self.now = self._receive

        # 取得し直す
        self._receive = set([])

    # 入力
    def _on(self, event_name:XUEventItem):
        if event_name in self._receive:
            raise ValueError(f"event_name:{event_name} is already registered.")
        self._receive.add(event_name)

    # キー入力イベント
    # *************************************************************************
    class Key:
        # キーイベント定義
        LEFT  = XUEventItem("CUR_L")
        RIGHT = XUEventItem("CUR_R")
        UP    = XUEventItem("CUR_U")
        DOWN  = XUEventItem("CUR_D")
        BTN_A = XUEventItem("BTN_A")
        BTN_B = XUEventItem("BTN_B")
        BTN_X = XUEventItem("BTN_X")
        BTN_Y = XUEventItem("BTN_Y")

        # インスタンスを作らず、クラスのまま使用する
        def __init__(self) -> None:
            raise PermissionError("This class is not instantiable")

        # まとめてアクセス
        @classmethod
        def LEFT_RIGHT(cls):
            return cls.LEFT, cls.RIGHT

        @classmethod
        def UP_DOWN(cls):
            return cls.UP, cls.DOWN

        @classmethod
        def CURSOR(cls):
            return *cls.LEFT_RIGHT(), *cls.UP_DOWN()

        @classmethod
        def ANY(cls):
            return *cls.CURSOR(), cls.BTN_A, cls.BTN_B, cls.BTN_X, cls.BTN_Y


# UIパーツの状態管理
# #############################################################################
class TreeException(RuntimeError):
    def __init__(self, elem:"XUElem", msg:str, *args: object):
        super().__init__(f"{elem.strtree()}\n{msg}", *args)

# XMLのElement管理
class XUElem:
    def __init__(self, xmlui:'XMLUI', element:Element):
        self._xmlui:XMLUI|None = xmlui  # ライブラリへのIF
        self._element = element  # 自身のElement

    @property
    def xmlui(self) -> "XMLUI":
        if self._xmlui is None:
            raise RuntimeError("This element is not attached to XMLUI.")
        return self._xmlui

    # UI_Elemは都度使い捨てなので、対象となるElementで比較する
    def __eq__(self, other) -> bool:
        if isinstance(other, XUElem):
            return other._element is self._element
        else:
            return super().__eq__(other)

    @classmethod
    def new(cls, xmlui:'XMLUI', tag_name:str) -> "XUElem":
        return XUElem(xmlui, Element(tag_name))

    # attribアクセス用
    # *************************************************************************
    def attr_int(self, key:str, default:int=0) -> int:
        return int(self._element.attrib.get(key, default))

    def attr_float(self, key:str, default:float=0) -> float:
        return float(self._element.attrib.get(key, default))

    def attr_str(self, key:str, default:str="") -> str:
        return self._element.attrib.get(key, default)

    def attr_bool(self, key:str, default:bool=False) -> bool:
        attr = self._element.attrib.get(key)
        return default if attr is None else attr.lower() == "true"

    def has_attr(self, key: str) -> bool:
        return key in self._element.attrib

    def set_attr(self, key:str|list[str], value: Any) -> Self:
        # attribはdict[str,str]なのでstrで保存する
        if isinstance(key, list):
            for i, k in enumerate(key):
                self._element.attrib[k] = str(value[i])
        else:
            self._element.attrib[key] = str(value)
        return self

    # tagアクセス用
    @property
    def tag(self) -> str:
        return self._element.tag

    # textアクセス用(基本はROで運用)
    @property
    def text(self) -> str:
        return "\n".join([line.strip() for line in self._element.text.splitlines()]) if self._element.text else ""

    def set_text(self, text:str) -> Self:
        self._element.text = text
        return self

    # その他
    # *************************************************************************
    @property
    def area(self) -> XURect:  # 親からの相対座標
        # areaは良く呼ばれるので、一回でもparent探しのdictアクセスを軽減する
        parent = self.parent
        parent_area = parent.area if parent else XURect(0, 0, self.xmlui.screen_w, self.xmlui.screen_h)

        # x,yはアトリビュートなので何度もアクセスしないように
        offset_x, offset_y = self.x, self.y

        # absがあれば絶対座標、なければ親からのオフセット
        return XURect(
            self.abs_x if self.has_attr("abs_x") else offset_x + parent_area.x,
            self.abs_y if self.has_attr("abs_y") else offset_y + parent_area.y,
            self.attr_int("w", parent_area.w - offset_x),
            self.attr_int("h", parent_area.h - offset_y)
        )

    def set_pos(self, x:int, y:int) -> Self:
        return self.set_attr(["x", "y"], [x, y])

    def set_abspos(self, x:int, y:int) -> Self:
        return self.set_attr(["abs_x", "abs_y"], [x, y])

    def set_wh(self, w:int, h:int) -> Self:
        return self.set_attr(["w", "h"], [w, h])

    # ツリー操作用
    # *************************************************************************
    @property
    def parent(self) -> 'XUElem|None':
        return self.xmlui._parent_cache.get(self._element, None)

    # 兄弟を先に取得するイテレータ
    # タブンElement.iter()も同じ挙動なんだけど、確証がないので手動
    def _rec_iter(self):
        # 兄弟を先に取得する
        for child in self._element:
            yield XUElem(self.xmlui, child)
        # 兄弟の後に子
        for child in self._element:
            yield from XUElem(self.xmlui, child)._rec_iter()

    @property
    def children(self) -> list["XUElem"]:
        return list(self._rec_iter())

    # 親以上祖先リスト
    @property
    def ancestors(self) -> 'list[XUElem]':
        out:list[XUElem] = []
        parent = self.parent
        while parent:
            out.append(parent)
            parent = parent.parent
        return out

    def find_by_id(self, id:str) -> 'XUElem':
        for child in self._rec_iter():
            if child.id == id:
                return child
        raise TreeException(self, f"ID '{id}' not found in '{self.tag}' and children")

    def find_by_tagall(self, tag:str) -> list['XUElem']:
        return [child for child in self._rec_iter() if child.tag == tag]

    # ツリーを遡って親を探す
    def find_parent_by_id(self, id:str) -> 'XUElem':
        parent = self.parent
        while parent:
            if parent.id == id:
                return parent
            parent = parent.parent
        raise TreeException(self, f"Parent '{id}' not found in '{self.tag}' parents")

    # openした親
    def find_owner(self) -> 'XUElem':
        return self.find_parent_by_id(self.owner)

    # すでにツリーに存在するか
    def exists_id(self, id:str) -> bool:
        for child in self._rec_iter():
            if child.id == id:
                return True
        return False

    def exists_tag(self, tag:str) -> bool:
        for child in self._rec_iter():
            if child.tag == tag:
                return True
        return False

    # 子を追加する
    def add_child(self, child:"XUElem"):
        # 削除済みを再利用はできない
        if child.removed:
            RuntimeError(f"Can't reuse removed child {child._element}")

        self._element.append(child._element)
        self.xmlui._parent_cache[child._element] = self

    # 子を全部削除する
    def clear_children(self):
        # clearでattribまで消えるので、attrに保存して戻す
        attr = self._element.attrib.copy()
        self._element.clear()
        self._element.attrib = attr

    # 自分を親から外す
    def remove(self):
        if self.parent is None:
            raise TreeException(self, f"Can't remove {self.tag}")
        self.parent._element.remove(self._element)

        # 子も全部removeはさすがに重いので、フラグ設定で済ませる
        for element in self._element.iter():  # iter()は自分も含まれる
            element.attrib["removed"] = "True"

    # open/close
    # *************************************************************************
    # 子に別Element一式を追加する
    def open(self, id:str, id_alias:str|None=None) -> "XUElem":
        # idがかぶらないよう別名を付けられる
        id_alias = id if id_alias is None else id_alias

        # IDがかぶってはいけない
        if self.xmlui.exists_id(id_alias):
            return self.xmlui.find_by_id(id_alias)

        # オープン
        opened:XUElem|None = None
        for template in self.xmlui._templates.values():
            # 複数のテンプレートの中から最初に見つかったidを複製してopenする
            if template.exists_id(id):
                opened = XUElem(self.xmlui, deepcopy(template.find_by_id(id)._element))
                self.add_child(opened)
                break
        if opened == None:
            raise RuntimeError(f"ID '{id}' not found in templates")

        # ownerを設定しておく
        for child in opened._rec_iter():
            child.set_attr("owner", id_alias)

        # open/closeが連続しないようTrg入力を落としておく
        self.xmlui.event.clear_trg()
        return opened

    # すぐにclose
    def close(self):
        # open/closeが連続しないようTrg入力を落としておく
        self.xmlui.event.clear_trg()

        # ownerが設定されていればownerを、無ければ自身をremoveする
        if self.owner and self.xmlui.exists_id(self.owner):
            target = self.xmlui.find_by_id(self.owner)
        else:
            target = self

        target.remove()

    # デバッグ用
    # *************************************************************************
    _strtree_count = 0
    def _rec_strtree(self, indent:str, pre:str) -> str:
        XUElem._strtree_count += 1
        out = pre + f"[{XUElem._strtree_count}] {self.tag}"
        out += f": {self.id}" if self.id else ""
        out += " " + str(self._element.attrib)
        for element in self._element:
            out += "\n" + XUElem(self.xmlui, element)._rec_strtree(indent, pre+indent)
        return out

    def strtree(self) -> str:
        XUElem._strtree_count = 0
        return self._rec_strtree("  ", "")

    # xmluiで特別な意味を持つアトリビュート一覧
    # わかりやすく全てプロパティを用意しておく(デフォルト値も省略せず書く)
    # 面倒でも頑張って書く
    # *************************************************************************
    @property
    def id(self) -> str:  # ID。xmlではかぶらないように(精神論)
        return self.attr_str("id", "")

    @property
    def value(self) -> str:  # 汎用値取得
        return self.attr_str("value", "")
    @value.setter
    def value(self, val:Any):  # element間汎用値持ち運び用
        self.set_attr("value", val)

    @property
    def action(self) -> str:  # イベント情報取得
        return self.attr_str("action", "")

    @property
    def selected(self) -> bool:  # 選択アイテムの選択状態
        return self.attr_bool("selected", False)

    @property
    def owner(self) -> str:  # close時のidを設定
        return self.attr_str("owner", "")

    @property
    def x(self) -> int:  # 親からの相対座標x
        return self.attr_int("x", 0)
    @property
    def y(self) -> int:  # 親からの相対座標y
        return self.attr_int("y", 0)
    @property
    def abs_x(self) -> int:  # 絶対座標x
        return self.attr_int("abs_x", 0)
    @property
    def abs_y(self) -> int:  # 絶対座標y
        return self.attr_int("abs_y", 0)
    @property
    def w(self) -> int:  # elementの幅
        return self.attr_int("w", self.xmlui.screen_w)
    @property
    def h(self) -> int:  # elementの高さ
        return self.attr_int("h", self.xmlui.screen_h)

    @property
    def update_count(self) -> int:  # updateが行われた回数
        return self.attr_int("update_count", 0)

    @property
    def use_event(self) -> str:  # eventの検知方法, listener or absorber or none
        return self.attr_str("use_event", XUEvent.UseEvent.NONE)

    @property
    def enable(self) -> bool:  # イベント有効フラグ(表示は使う側でどうするか決める)
        return self.attr_bool("enable", True)
    @enable.setter
    def enable(self, enable_:bool) -> bool:
        self.set_attr("enable", enable_)
        return enable_

    @property
    def removed(self) -> bool:  # 内部管理用削除済みフラグ
        return self.attr_bool("removed", False)


# XMLでUIライブラリ本体
# #############################################################################
class XMLUI(XUElem):
    debug_enable = False  # デバッグから参照するフラグ(クラス変数≒システムで一意)

    # 初期化
    # *************************************************************************
    # 初期化。<xmlui>を持つXMLを突っ込む
    def __init__(self, screen_w:int, screen_h:int):
        # rootを作って自分自身に設定
        xmlui = Element("xmlui")
        xmlui.attrib["id"] = "xmlui"
        super().__init__(self, xmlui)

        # ウインドウサイズを記憶
        self.screen_w = screen_w
        self.screen_h = screen_h

        # キャッシュ
        self._parent_cache:dict[Element, XUElem] = {}  # dict[child] = parent_state

        # XMLテンプレート置き場
        self._templates:dict[str,XUElem] = {}  # dict[file_path, dom]

        # 処理関数の登録
        self._draw_funcs:dict[str, Callable[[XUElem, XUEvent], str|None]] = {}

        # イベント管理
        self.event = XUEvent(True)  # 唯一のactiveとする

        # 描画ツリー構築
        self.root = XUElem.new(self, "root").set_attr("id", "root")
        self._over = XUElem.new(self, "oevr").set_attr("id", "over")
        self.add_child(self.root)  # 普通に使うもの
        self.add_child(self._over)  # 上に強制で出す物

    # XMLUIそのものを閉じる
    def close(self):
        # templateの削除
        self._templates = {}

        # 登録関数のクリア
        self._draw_funcs = {}

        # ワーキングツリー全体の参照を全て削除
        for element in self.xmlui._element.iter():
            element.clear()

        # 自己参照を外す
        self.xmlui._xmlui = None
        self.root._xmlui = None
        self._over._xmlui = None

        # キャッシュの削除
        self._parent_cache = {}

    # ユーティリティークラス作成用
    class HasRef:
        def __init__(self, xmlui:"XMLUI"):
            self.xmlui = xmlui

    # template操作
    # *************************************************************************
    # ファイルから読み込み(ファイル読み込み失敗は例外に任せる)
    def load_template(self, xml_filename:str):
        f= open(xml_filename, "r", encoding="utf8")
        self._templates[xml_filename] = XUElem(self, xml.etree.ElementTree.fromstring(f.read()))

        # デバッグ時はIDがかぶってないかチェック
        if XMLUI.debug_enable:
            ids = []
            for template in self._templates.values():
                for child in template._rec_iter():
                    if child.id:
                        if child.id in ids:
                            raise RuntimeError(f"ID '{child.id}' is duplicated in '{xml_filename}'")
                        ids.append(child.id)

    # 開発用。テンプレートを読み込み直す
    def reload_templates(self):
        for xml_filename in self._templates.keys():
            self.load_template(xml_filename)

    # 処理関数登録
    # *************************************************************************
    def set_drawfunc(self, tag_name:str, func:Callable[[XUElem,XUEvent], str|None]):
        # 処理関数の登録
        self._draw_funcs[tag_name] = func

    def clear_drawfunc(self):
        self._draw_funcs = {}

    # デコレータも用意
    def tag_draw(self, tag_name:str):
        def wrapper(bind_func:Callable[[XUElem,XUEvent], str|None]):
            self.set_drawfunc(tag_name, bind_func)
        return wrapper

    # 更新
    # *************************************************************************
    def draw(self):
        # イベントの更新
        self.event.update()

        # ActiveStateの取得。Active=最後、なので最後から確認
        active_elems:list[XUElem] = []
        for event in reversed([elem for elem in self._rec_iter()
                                if elem.enable
                                    and (elem.use_event == XUEvent.UseEvent.ABSORBER
                                    or elem.use_event == XUEvent.UseEvent.LISTENER)]):
            active_elems.append(event)  # イベントを使うelemを回収
            if event.use_event == XUEvent.UseEvent.ABSORBER:  # イベント通知終端
                break

        # 親情報の更新
        self._parent_cache = {c:XUElem(self, p) for p in self._element.iter() for c in p}

        # 更新処理
        for elem in self.children:  # 中でTreeを変えたいのでイテレータではなくリストで
            # 前の処理までで削除済みなら何もしない
            if elem.removed:
                continue

            # active/inactiveどちらのeventを使うか決定
            event = deepcopy(self.event) if elem in active_elems else XUEvent()

            # updateカウンタ更新
            event.on_init = elem.update_count == 0  # やっぱりinitialize情報がどこかに欲しい
            elem.set_attr("update_count", elem.update_count+1)  # 1スタート(0は初期化時)

            # 登録されている関数を実行。戻り値はイベント
            if elem.tag in self._draw_funcs:
                result = self._draw_funcs[elem.tag](elem, event)
                if result is not None:
                    self.on(result)

        # 最後に自分もカウントアップ
        self.set_attr("update_count", self.update_count+1)

    # イベント
    # *************************************************************************
    # イベントを記録する。Trg処理は内部で行っているので現在の状態を入れる
    def on(self, event_name:str):
        self.event._on(XUEventItem(event_name))

    # イベントが発生していればopenする。すでに開いているチェック付き
    def open_by_event(self, event_names:list[str]|str, id:str, id_alias:str|None=None) -> XUElem|None:
        if isinstance(event_names, str):
            event_names = [event_names]  # 配列で統一
        for event_name in event_names:
            if event_name in self.event.trg:
                return self.root.open(id, id_alias)
        return None

    # override
    def open(self, id:str, id_alias:str|None=None) -> XUElem:
        return self.root.open(id, id_alias)

    # over側で開く
    def popup(self, id:str, id_alias:str|None=None) -> XUElem:
        return self._over.open(id, id_alias)


# ユーティリティークラス
# #############################################################################
# 基本は必要な情報をツリーでぶら下げる
# Treeが不要ならたぶんXUStateで事足りる
class _XUUtilBase(XUElem):
    def __init__(self, elem:XUElem, root_tag:str):
        super().__init__(elem.xmlui, elem._element)

        # 自前設定が無ければabsorberにしておく
        if not self.has_attr("use_event"):
            self.set_attr("use_event", XUEvent.UseEvent.ABSORBER)

        # UtilBase用ルートの作成(状態保存先)
        if elem.exists_tag(root_tag):
            self._util_info = elem.find_by_tagall(root_tag)[0]
        else:
            self._util_info = XUElem.new(elem.xmlui, root_tag)
            elem.add_child(self._util_info)

# メニュー系
# *****************************************************************************
# 選択クラス用アイテム
class XUSelectItem(XUElem):
    def __init__(self, elem:XUElem):
        super().__init__(elem.xmlui, elem._element)

# 選択ベース
class XUSelectInfo(_XUUtilBase):
    # クラス定数
    INFO_TAG = "_xmlui_select_info"
    ITEM_TAG = "_xmlui_select_item"

    def __init__(self, elem:XUElem):
        super().__init__(elem, self.INFO_TAG)

    # 処理を途中で抜けるならこっちが早い
    @property
    def item_iter(self):
        # 直下のみ対象。別の選択が下にくっつくことがあるので下まではみない
        for child in self._util_info._element:
            if child.tag == self.ITEM_TAG:
                yield XUSelectItem(XUElem(self.xmlui, child))

    # listでまとめて返す。扱いやすい
    @property
    def items(self) -> list[XUSelectItem]:
        return list(self.item_iter)

    # 選択中のitemの番号(Treeの並び順)
    @property
    def selected_no(self) -> int:
        for i,item in enumerate(self.item_iter):
            if item.selected:
                return i
        return 0  # デフォルト

    # 選択中のitem
    @property
    def selected_item(self) -> XUSelectItem:
        return self.items[self.selected_no]

    # itemの数
    @property
    def item_num(self) -> int:
        return len(self.items)

    # __eq__だとpylanceの型認識がおかしくなるのでactionを使う
    @property
    def action(self) -> XUEventItem:
        return XUEventItem(self.selected_item.action)

# XUSelectBase書き込み用
class XUSelectBase(XUSelectInfo):
    def __init__(self, elem:XUElem, item_tag:str, rows:int, item_w:int, item_h:int):
        super().__init__(elem)

        # infoタグの下になければ自分の直下から探してコピーする
        if not self.items and item_tag:
            for i,child in enumerate([child for child in self._element if child.tag == item_tag]):
                # タグ名は専用のものに置き換え
                item = XUSelectItem(XUElem(elem.xmlui, deepcopy(child)))
                item._element.tag = self.ITEM_TAG
                self._util_info.add_child(item)

                # 初期座標
                item.set_pos(item.x + i % rows * item_w, item.y + i // rows * item_h)

        # 操作の時に使うので覚えておく
        self.rows = rows

        # 選択状態復帰
        self.select(self.selected_no)

    # 値設定用
    # -----------------------------------------------------
    # 選択追加アトリビュートに設定する(元のXMLを汚さない)
    def select(self, no:int):
        for i,item in enumerate(self.items):
            item.set_attr("selected", i == no)

    # 選択を移動させる
    def next(self, add_x:int, add_y:int, x_wrap=False, y_wrap=False):
        # キャッシュ
        no = self.selected_no
        item_num = self.item_num

        # 行と列の状態取得(半端グリッド対応)
        rows = [self.rows for _ in range(item_num // self.rows)]
        if item_num % self.rows != 0:
            rows.append(item_num % self.rows)
        cols = [item_num//self.rows for i in range(self.rows)]
        for i in range(item_num % self.rows):
            cols[i] += 1

        # 更新
        x = no % self.rows
        y = no // self.rows
        next_x = x + add_x
        next_y = y + add_y

        # wrapモードとmin/maxモードそれぞれで更新後状態調整
        if next_x < 0:
            next_x = rows[y]-1 if x_wrap else x
        if next_x >= rows[y]:
            next_x = 0 if x_wrap else x
        if next_y < 0:
            next_y = cols[next_x]-1 if y_wrap else y
        if next_y >= cols[next_x]:
            next_y = 0 if x_wrap else y

        self.select(next_y*self.rows + next_x)

# グリッド選択
class XUSelectGrid(XUSelectBase):
    def __init__(self, elem:XUElem, item_tag:str, rows:int, item_w:int, item_h:int):
        super().__init__(elem, item_tag, rows, item_w, item_h)

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
class _XUSelectListBase(XUSelectBase):
    def __init__(self, elem:XUElem, item_tag:str, rows:int, item_w:int, item_h:int):
        super().__init__(elem, item_tag, rows, item_w, item_h)
        self.next_move = [0, 0]

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
class XUSelectList(_XUSelectListBase):
    def __init__(self, elem:XUElem, item_tag:str, item_h:int):
        super().__init__(elem, item_tag, 1, 0, item_h)
        self.next_move = [0, 1]  # 上下で動く

# 横方向リスト
class XUSelectRowList(_XUSelectListBase):
    def __init__(self, elem:XUElem, item_tag:str, item_w:int):
        super().__init__(elem, item_tag, len(elem.find_by_tagall(item_tag)), item_w, 0)
        self.next_move = [1, 0]  # 左右で動く


# テキスト系
# *****************************************************************************
# 半角を全角に変換
_from_hanakaku = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_to_zenkaku = "０１２３４５６７８９ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
_from_hanakaku += " !\"#$%&'()*+,-./:;<=>?@[]^_`{|}~"  # 半角記号を追加
_to_zenkaku += "　！＂＃＄％＆＇（）＊＋，－．／：；＜＝＞？＠［］＾＿｀｛｜｝～"  # 全角記号を追加
_hankaku_zenkaku_dict = str.maketrans(_from_hanakaku, _to_zenkaku)

# テキストパラメータ変換
class XUTextUtil:
    SEPARATE_REGEXP = r"\\n"  # 改行に変換する正規表現(\nへ)
    PAGE_REGEXP = r"\\p"  # 改ページに変換する正規表現(\0へ)

    # 置き換えパラメータの抜き出し
    # -----------------------------------------------------
    # キーを抜き出し
    @classmethod
    def find_params(cls, text) -> set[str]:
        params = re.findall(r"{(\S+?)}", text)
        return set([param.split(":")[0] for param in params])  # :以降を取り除く

    # 辞書で抜き出し
    @classmethod
    def find_params_dict(cls, text:str, all_params:dict[str,Any]) -> dict[str,Any]:
        out:dict[str,Any] = {}
        for param in cls.find_params(text):
            out[param] = all_params[param]
        return out

    # パラメータを置き換える(\n\0置換も行う)
    # -----------------------------------------------------
    @classmethod
    def format_dict(cls, text:str, all_params:dict[str,Any]={}) -> str:
        tmp_text = re.sub(cls.PAGE_REGEXP, "\0", text)  # \pという文字列をNullに
        tmp_text = re.sub(cls.SEPARATE_REGEXP, "\n", tmp_text)  # \nという文字列を改行コードに
        return tmp_text.format(**cls.find_params_dict(tmp_text, all_params)) if all_params else tmp_text

    # 文字列中の半角を全角に変換する
    @classmethod
    def format_zenkaku(cls, val:str|int|float, all_params:dict[str,Any]={}) -> str:
        val = cls.format_dict(str(val), all_params)  # \n\pを先に変換しておく
        return unicodedata.normalize("NFKC", val).translate(_hankaku_zenkaku_dict)

    # その他
    # -----------------------------------------------------
    # 改行・改ページを抜いた文字数カウント
    @classmethod
    def length(cls, text:str) -> int:
        return len(re.sub("\n|\0", "", text))

# アニメーションテキストページ
class XUPageItem(XUSelectItem):
    DRAW_COUNT_ATTR = "_xmlui_text_count"

    # 表示カウンタ操作
    # -----------------------------------------------------
    # 現在の表示文字数
    @property
    def draw_count(self) -> float:
        return float(self.attr_float(self.DRAW_COUNT_ATTR, 0))

    @draw_count.setter
    def draw_count(self, count:float) -> float:
        self.set_attr(self.DRAW_COUNT_ATTR, count)
        return count

    # アニメーション用
    # -----------------------------------------------------
    # draw_countまでの文字列を改行分割。スライスじゃないのは改行を数えないため
    @classmethod
    def _limitstr(cls, tmp_text:str, text_count:float) -> str:
        limit = math.ceil(text_count)

        # limitまで縮める
        for i,c in enumerate(tmp_text):
            if (limit := limit if ord(c) < 0x20 else limit-1) < 0:  # 改行は数えない
                return tmp_text[:i]
        return tmp_text

    # 改行を抜いた文字数よりカウントが大きくなった
    @property
    def is_finish(self) -> bool:
        return self.draw_count >= self.length

    # 一気に表示
    @property
    def finish(self) -> Self:
        self.draw_count = self.length
        return self

    # draw_countまでのテキストを受け取る
    @property
    def text(self) -> str:
        return self._limitstr(super().text, self.draw_count)

    # draw_countまでのテキストを全角で受け取る
    @property
    def zenkaku(self) -> str:
        return XUTextUtil.format_zenkaku(self.text)

    # テキスト全体
    # -----------------------------------------------------
    # 全体テキストを受け取る
    @property
    def all_text(self) -> str:
        return super().text

    # テキスト全体の長さ(\n\0抜き)
    @property
    def length(self) -> int:
        return XUTextUtil.length(super().text)

    # 行
    # -----------------------------------------------------
    # 現在の行番号
    @property
    def current_line_no(self) -> int:
        return max(0, len(self.text.splitlines())-1)

    # 現在の行テキスト
    @property
    def current_line(self) -> str:
        lines = self.text.splitlines()
        return lines[self.current_line_no] if lines else ""

    # 現在の行の全体の長さ
    @property
    def current_line_length(self):
        return len(self.all_text.splitlines()[self.current_line_no])


# ページをセレクトアイテムで管理
class XUPageInfo(XUSelectBase):
    def __init__(self, elem:XUElem):
        super().__init__(elem, "", 1, 0, 0)

    # ページ操作
    # -----------------------------------------------------
    # 現在ページ番号
    @property
    def current_page_no(self) -> int:
        return self.selected_no

    # ページテキスト
    # -----------------------------------------------------
    # 現在ページのアニメーション情報アクセス
    @property
    def current_page(self):
        return XUPageItem(self.items[self.current_page_no])

    # ただの型キャスト。中身はitems
    @property
    def pages(self) -> list[XUPageItem]:
        return [XUPageItem(item) for item in self.items]

    # 次ページがなくテキストは表示完了 = 完全に終了
    @property
    def is_all_finish(self):
        if not self.items:  # テキストがない
            return True
        return not self.is_next_wait and self.current_page.is_finish

    # 次ページあり
    @property
    def is_next_wait(self):
        if not self.items:  # テキストがない
            return False
        return self.current_page.is_finish and self.current_page_no < self.item_num-1

    # ツリー操作
    # -----------------------------------------------------
    # テキストをページ分解してツリーにぶら下げる。作ったページを返す
    def add_pages(self, text:str, page_line_num:int, wrap:int) -> list[XUPageItem]:
        pages:list[XUPageItem] = []
        for page_text in XUPageText.split_page_texts(text, page_line_num, wrap):
            page_item = XUPageItem(XUElem.new(self.xmlui, self.ITEM_TAG))
            self._util_info.add_child(page_item.set_text(page_text))

            pages.append(page_item)  # return用
        return pages

    def clear_pages(self):
        for child in self._util_info.find_by_tagall(self.ITEM_TAG):
            child.remove()

class XUPageText(XUPageInfo):
    def __init__(self, elem:XUElem, page_line_num:int=1024, wrap:int=4096):
        super().__init__(elem)
        self.page_line_num = page_line_num
        self.wrap = wrap

        # ページ未登録なら登録しておく
        if not self.pages and self.text.strip():
            self.add_pages(self.text, page_line_num, wrap)

    # ページごとに行・ワードラップ分割
    @classmethod
    def split_page_lines(cls, text:str, page_line_num:int, wrap:int) -> list[list[str]]:
        wrap = max(wrap, 1)   # 0だと無限になってしまうので最低1を入れておく

        # 行数でページ分解
        pages:list[list[str]] = []
        for page_text in text.split("\0"):
            lines:list[str] = []
            for line in sum([[line[i:i+wrap] for i in  range(0, len(line), wrap)] for line in page_text.splitlines()], []):
                lines.append(line)
                if len(lines) >= page_line_num:
                    pages.append(lines)
                    lines = []
            if lines:  # 最後の残り
                pages.append(lines)
        return pages

    # ページごとテキスト(行・ワードラップ分割は\n結合)
    @classmethod
    def split_page_texts(cls, text:str, page_line_num:int, wrap:int) -> list[str]:
        return ["\n".join(page) for page in cls.split_page_lines(text, page_line_num, wrap)]

    # ページ操作
    # -----------------------------------------------------
    # ページ設定
    def set_page_no(self, no:int=0) -> Self:
        # ページを切り替えたときはカウンタをリセット
        if self.current_page_no != no:
            self.current_page.draw_count = 0
        self.select(no)
        return self

    # 次のページへ
    def next_page(self):
        self.set_page_no(self.current_page_no+1)


# ウインドウサポート
# *****************************************************************************
class XUWinBase(XUElem):
    # ウインドウの状態定義
    STATE_OPENING = "opening"
    STATE_OPENED = "opened"
    STATE_CLOSING = "closing"
    STATE_CLOSED = "closed"

    # 状態を保存するアトリビュート
    WIN_STATE_ATTR = "_xmlui_win_state"
    OPENING_COUNT_ATTR = "_xmlui_opening_count"
    CLOSING_COUNT_ATTR = "_xmlui_closing_count"

    # 状態管理
    # -----------------------------------------------------
    def __init__(self, state:XUElem):
        super().__init__(state.xmlui, state._element)

        # ステートがなければ用意しておく
        if not self.has_attr(self.WIN_STATE_ATTR):
            self.win_state = self.STATE_OPENING

    # override。closeするときに状態をCLOSEDにする
    def close(self):
        self.win_state = self.STATE_CLOSED  # finish
        super().close()

    # XUWinBaseを使ったElementかどうか。attributeの有無でチェック
    @classmethod
    def is_win(cls, state:XUElem) -> bool:
        return state.has_attr(cls.WIN_STATE_ATTR)

    # 一番近いXUWinBaseを持つ親を取得する
    @classmethod
    def find_parent_win(cls, state:XUElem) -> "XUWinBase":
        for parent in state.ancestors:
            if XUWinBase.is_win(parent):
                return XUWinBase(parent)
        raise TreeException(state.xmlui, "Window not found in parents")

    # ウインドウの状態管理
    # -----------------------------------------------------
    # ウインドウの状態に応じてカウンタを更新する。状態は更新しない
    def update(self):
        win_state = self.attr_str(self.WIN_STATE_ATTR)
        match win_state:
            case self.STATE_OPENING:
                self.set_attr(self.OPENING_COUNT_ATTR, self.attr_int(self.OPENING_COUNT_ATTR) + 1)
            case self.STATE_CLOSING:
                self.set_attr(self.CLOSING_COUNT_ATTR, self.attr_int(self.CLOSING_COUNT_ATTR) + 1)

    # ウインドウの状態のset/get
    @property
    def win_state(self) -> str:
        return self.attr_str(self.WIN_STATE_ATTR)

    @win_state.setter
    def win_state(self, win_state:str) -> str:
        self.set_attr(self.WIN_STATE_ATTR, win_state)
        return win_state

    # opning/closingの状態管理
    # -----------------------------------------------------
    # 現在open中かどうか。open完了もTrue
    @property
    def is_opening(self):
        return self.win_state == self.STATE_OPENING or self.win_state == self.STATE_OPENED

    # 現在close中かどうか。close完了もTrue
    @property
    def is_closing(self):
        return self.win_state == self.STATE_CLOSING or self.win_state == self.STATE_CLOSED

    # openされてからのカウント(≒update_count)
    @property
    def opening_count(self) -> int:
        return self.attr_int(self.OPENING_COUNT_ATTR)

    # closingが発生してからのcount
    @property
    def closing_count(self) -> int:
        return self.attr_int(self.CLOSING_COUNT_ATTR)

    # 子も含めてclosingにする
    def start_close(self):
        self.enable = False  # closingは実質closeなのでイベントは見ない
        self.win_state = self.STATE_CLOSING

        # 子も順次closing
        for child in self._rec_iter():
            child.enable = False  # 全ての子のイベント通知をoffに
            if XUWinBase.is_win(child):  # 子ウインドウも一緒にクローズ
                XUWinBase(child).win_state = self.STATE_CLOSING


# ゲージサポート
# *****************************************************************************
class XUGageBase(XUElem):
    # 隙間サイズ(px)
    # 数値最大(=ゲージ分割数)
    # XURectで分割ゲージの各Box
    pass
