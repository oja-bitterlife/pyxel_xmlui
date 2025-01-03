import sqlite3

# DB関係
# ゲームではストレージに書き込まないのでmemory_dbに移して使う
class XUXMemoryDB:
    # コネクションラッパー。通常自分で呼び出すことはない
    def __init__(self, conn:sqlite3.Connection):
        self._conn:sqlite3.Connection = conn
        self._conn.row_factory = sqlite3.Row 

    # 空のメモリDB作成。主にデバッグ用
    @classmethod
    def empty(cls) -> sqlite3.Cursor:
        conn = sqlite3.connect(":memory:")
        return XUXMemoryDB(conn).cursor()

    # DBを読み込んでメモリDB上に展開する
    @classmethod
    def load(cls, db_path) -> sqlite3.Cursor:
        conn = sqlite3.connect(":memory:")
        with open(db_path, "rb") as f:
            conn.deserialize(f.read())
        return XUXMemoryDB(conn).cursor()

    # 閉じる、、、んだけど、たぶんcursor.connection.close()を呼ぶ気がする
    # :memory:なので閉じ忘れても特に問題はないはず
    def close(self):
        self._conn.close()

    # 新しいカーソルを作成する
    def cursor(self) -> sqlite3.Cursor:
        return self._conn.cursor()
