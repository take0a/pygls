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
"""これは、:lsp:`textDocument/documentColor` リクエストと 
:lsp:`textDocument/colorPresentation` リクエストを実装します。

これらのメソッドを組み合わせることで、言語クライアントにドキュメント内に表示される色を
認識し、表示する方法を教えることができます。
例として、CSS ファイルで色を記述するさまざまな方法を考えてみましょう。

- ``black``
- ``#000``
- ``#000000``
- ``rgb(0, 0, 0)``
- ``hsl(...)``
- など。

`textDocument/documentColor`` リクエストを実装することで、ドキュメント内で色を表す
すべての場所と、それに相当する RGBA 値をクライアントに伝えることができます。
`VSCode <https://code.visualstudio.com/docs/languages/css#_syntax-coloring-color-preview>`__ 
では、これらの場所は色値の横にある小さな色付きの四角で表されます。

一部のエディター（VSCode など）はカラーピッカーも提供しています。
``textDocument/colorPresentation`` リクエストを実装することで、RGBA カラー値を
ドキュメント構文における同等の表現に変換できます。
これにより、ユーザーはテキストエディター内から簡単に新しいカラー値を選択できるようになります。

このサーバーは、CSS の 16 進カラーコード構文（``#000`` および ``#000000``）に対して
上記で定義されたリクエストを実装しています。
"""

import logging
import re

from lsprotocol import types

from pygls.cli import start_server
from pygls.lsp.server import LanguageServer

COLOR = re.compile(r"""\#([a-fA-F0-9]{6}|[a-fA-F0-9]{3})(?!\w)""")
server = LanguageServer("color-server", "v1")


@server.feature(
    types.TEXT_DOCUMENT_DOCUMENT_COLOR,
)
def document_color(params: types.CodeActionParams):
    """ドキュメント内で宣言された色のリストを返します。"""
    items = []
    document_uri = params.text_document.uri
    document = server.workspace.get_text_document(document_uri)

    for linum, line in enumerate(document.lines):
        for match in COLOR.finditer(line.strip()):
            start_char, end_char = match.span()

            # これはショートフォームカラーですか？
            if (end_char - start_char) == 4:
                color = "".join(c * 2 for c in match.group(1))
                value = int(color, 16)
            else:
                value = int(match.group(1), 16)

            # 単一のカラー値を各カラー チャネルの値に分割します。
            blue = (value & 0xFF) / 0xFF
            green = (value & (0xFF << 8)) / (0xFF << 8)
            red = (value & (0xFF << 16)) / (0xFF << 16)

            items.append(
                types.ColorInformation(
                    color=types.Color(red=red, green=green, blue=blue, alpha=1.0),
                    range=types.Range(
                        start=types.Position(line=linum, character=start_char),
                        end=types.Position(line=linum, character=end_char),
                    ),
                )
            )

    return items


@server.feature(
    types.TEXT_DOCUMENT_COLOR_PRESENTATION,
)
def color_presentation(params: types.ColorPresentationParams):
    """色を指定すると、その色の表現をドキュメントに挿入する方法を
    クライアントに指示します。"""
    color = params.color

    b = int(color.blue * 255)
    g = int(color.green * 255)
    r = int(color.red * 255)

    # 各カラーチャンネルを単一の値に結合する
    value = (r << 16) | (g << 8) | b
    return [types.ColorPresentation(label=f"#{value:0{6}x}")]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    start_server(server)
