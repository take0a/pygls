############################################################################
# Copyright(c) Open Law Library. All rights reserved.                      #
# See ThirdPartyNotices.txt in the project root for additional notices.    #
#                                                                          #
# Licensed under the Apache License, Version 2.0 (the "License")           #
# you may not use this file except in compliance with the License.         #
# You may obtain a copy of the License at                                  #
#                                                                          #
#     http: // www.apache.org/licenses/LICENSE-2.0                         #
#                                                                          #
# Unless required by applicable law or agreed to in writing, software      #
# distributed under the License is distributed on an "AS IS" BASIS,        #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. #
# See the License for the specific language governing permissions and      #
# limitations under the License.                                           #
############################################################################
"""このサンプル サーバーは、別のスレッドでメッセージ ハンドラーを実行する pygls の
機能を示しています。

"""
from __future__ import annotations

import time
import threading

from lsprotocol import types

from pygls.cli import start_server
from pygls.lsp.server import LanguageServer

server = LanguageServer("threaded-server", "v1")


@server.feature(
    types.TEXT_DOCUMENT_COMPLETION,
    types.CompletionOptions(trigger_characters=["."]),
)
def completions(params: types.CompletionParams | None = None) -> types.CompletionList:
    """完了アイテムを返します。"""
    return types.CompletionList(
        is_incomplete=False,
        items=[
            types.CompletionItem(label="one"),
            types.CompletionItem(label="two"),
            types.CompletionItem(label="three"),
            types.CompletionItem(label="four"),
            types.CompletionItem(label="five"),
        ],
    )


@server.command("count.down.blocking")
def count_down_blocking(ls: LanguageServer, *args):
    """カウントダウンを開始し、同期的にメッセージを表示します。
    メインスレッドをブロックしますが、完了項目を表示してみることでテストできます。
    """
    thread = threading.current_thread()
    for i in range(10):
        ls.window_show_message(
            types.ShowMessageParams(
                message=f"Counting down in thread {thread.name!r} ... {10 - i}",
                type=types.MessageType.Info,
            ),
        )
        time.sleep(1)


@server.thread()
@server.command("count.down.thread")
def count_down_thread(ls: LanguageServer, *args):
    """カウントダウンを開始し、別のスレッドにメッセージを表示します。
    メインスレッドはブロックされません。完了項目を表示してみることで、
    メインスレッドをブロックしないかどうかを確認できます。
    """
    thread = threading.current_thread()

    for i in range(10):
        ls.window_show_message(
            types.ShowMessageParams(
                message=f"Counting down in thread {thread.name!r} ... {10 - i}",
                type=types.MessageType.Info,
            ),
        )
        time.sleep(1)


@server.thread()
@server.command("count.down.error")
def count_down_error(ls: LanguageServer, *args):
    """エラーをスローするスレッド ハンドラー。"""
    1 / 0


if __name__ == "__main__":
    start_server(server)
