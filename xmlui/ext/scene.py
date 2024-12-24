from typing import Callable
import pyxel

from xmlui.core import XMLUI
from xmlui.ext.input import XUXInput
from xmlui.ext.timer import XUXTimeout


# ステータス遷移管理用。NPCの寸劇とかで使うやつ
# #############################################################################
# 一定時間後に1つのaction。アクションをつなげて実行する場合は主にこちら
class XUXActItem(XUXTimeout):
    # デフォルトはすぐ実行
    def __init__(self):
        super().__init__(0)
        self._init_func:Callable|None = self.init

    # コンストラクタではなくinit()の中で時間を設定する。
    def set_wait(self, wait:int):
        self._count_max = wait

    # オーバーライドして使う物
    def init(self):
        pass

# 一定時間内ずっとwaigingが実行され、最後にaction。
class XUXActWait(XUXActItem):
    WAIT_FOREVER = 2**31-1

    # デフォルトは無限待機
    def __init__(self):
        super().__init__()
        self.set_wait(self.WAIT_FOREVER)

    # override
    @property
    def alpha(self):
        if self._count_max == self.WAIT_FOREVER:
            return 1
        else:
            return super().alpha

    # override
    def update(self) -> bool:
        if not self.is_finish:
            if self.waiting():
                self.finish()
        return super().update()

    # オーバーライドして使う物
    def waiting(self) -> bool:
        return False

# Act管理クラス。各Itemをコレに登録していく
# *****************************************************************************
class XUXAct:
    def __init__(self):
        self.queue:list[XUXActItem] = []

    def add(self, *items:XUXActItem):
        for item in items:
            self.queue.append(item)

    def next(self):
        if not self.is_empty:
            self.queue.pop(0)

    def update(self):
        if not self.is_empty:
            act = self.current_act
            if act._init_func:
                act._init_func()  # 初回はinitも実行
                act._init_func = None
            act.update()

            # 完了したら次のAct
            if act.is_finish:
                self.next()

    @property
    def current_act(self):
        return self.queue[0]

    @property
    def is_empty(self) -> bool:
        return len(self.queue) == 0


# シーン管理(フェードイン・フェードアウト)用
# #############################################################################
# シーン管理用仕込み
class _XUXSceneBase:
    def __init__(self):
        self._next_scene:XUXScene|None = None
        self.is_end = False

    # シーン遷移
    def set_next_scene(self, scene:"XUXScene"):
        self._next_scene = scene

    # オーバーライドして使う物
    def update_scene(self):
        pass
    def draw_scene(self):
        pass

# シーンクラス。継承して使おう
class XUXScene(_XUXSceneBase):
    # デフォルトフェードカラー
    FADE_COLOR = 0

    # デフォルトフェードインアウト時間
    OPEN_COUNT = 15
    CLOSE_COUNT = 30

    # フェード管理
    # -----------------------------------------------------
    class FadeAct(XUXAct):
        def __init__(self):
            super().__init__()
            self.alpha:float = 0.0

    # 各フェードパート
    # -----------------------------------------------------
    # パートベース。fade_actのalphaを書き換える
    class _FadeActItem(XUXActWait):
        def __init__(self, fade_act:"XUXScene.FadeAct"):
            super().__init__()
            self.fade_act = fade_act

    # フェードイン
    class FadeIn(_FadeActItem):
        def __init__(self, fade_act:"XUXScene.FadeAct", open_count:int):
            super().__init__(fade_act)
            self.set_wait(open_count)

        def waiting(self) -> bool:
            self.fade_act.alpha = 1-self.alpha  # 黒から
            return self.is_finish

    # フェードアウト
    class FadeOut(_FadeActItem):
        def waiting(self) -> bool:
            self.fade_act.alpha = self.alpha
            return False

    # シーンメイン
    class SceneMain(_FadeActItem):
        def waiting(self) -> bool:
            self.fade_act.alpha = 0
            return False

    # 初期化
    # -----------------------------------------------------
    def __init__(self, xmlui:XMLUI, open_count=OPEN_COUNT):
        super().__init__()
        self.xmlui = xmlui

        # フェードインから
        self.fade_act = XUXScene.FadeAct()
        self.fade_act.add(
            XUXScene.FadeIn(self.fade_act, open_count),
            XUXScene.SceneMain(self.fade_act),
            XUXScene.FadeOut(self.fade_act))

    # mainから呼び出すもの
    # -----------------------------------------------------
    def update_scene(self):
        # フェードアウトが終わった
        if self.fade_act.is_empty:
            self.is_end = True  # シーン完了。endでシーン遷移しておくように
            self.end()
            return

        if not isinstance(self.fade_act.current_act, XUXScene.FadeOut):
            # 更新処理呼び出し
            XUXInput(self.xmlui).check()  # UI用キー入力
            self.update()

        self.fade_act.update()

    def draw_scene(self):
        pyxel.dither(1.0)  # 戻しておく

        # フェード描画
        # -------------------------------------------------
        # Actがない(=シーン切り替え中)
        if self.fade_act.is_empty:
            self.fade_act.alpha = 1  # 常に塗りつぶす
            pyxel.rect(0, 0, self.xmlui.screen_w, self.xmlui.screen_h, self.FADE_COLOR)

        # Actがある(=シーン中)
        else:
            self.draw()

            # 無駄な描画をしないよう
            if self.fade_act.alpha > 0:
                pyxel.dither(self.fade_act.alpha)  # フェードで
                pyxel.rect(0, 0, self.xmlui.screen_w, self.xmlui.screen_h, self.FADE_COLOR)

    def end_scene(self, close_count=CLOSE_COUNT):
        # シーンメイン時以外から呼び出されたらなにもしないように
        if isinstance(self.fade_act.current_act, XUXScene.SceneMain):
            self.fade_act.next()
            self.fade_act.current_act.set_wait(close_count)

    # オーバーライドして使う物
    # これらはsceneの中から呼び出すように(自分で呼び出さない)
    # -----------------------------------------------------
    def update(self):
        pass
    def draw(self):
        pass
    def end(self):
        pass


# シーン管理用
# *****************************************************************************
class XUXSceneManager:
    def __init__(self, start_scene:_XUXSceneBase):
        self.current_scene:_XUXSceneBase = start_scene

    def update(self):
        # next_sceneが設定されていたら
        if self.current_scene._next_scene is not None:
            self.current_scene = self.current_scene._next_scene
            self.current_scene._next_scene = None

        # updateはend以降は呼ばない
        if not self.current_scene.is_end:
            self.current_scene.update_scene()

    def draw(self):
        # drawはend以降も呼ぶ(endの状態を描画)
        self.current_scene.draw_scene()
