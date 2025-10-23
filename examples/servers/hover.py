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
"""これは :lsp:`textDocument/hover` リクエストを実装します。

通常、このメソッドはユーザーがドキュメント内のシンボル上にマウスまたはカーソルを
置いたときに呼び出され、選択されたシンボルに関するドキュメントを提供できます。

このサーバーは、様々な日時表現に対応する `textDocument/hover` を実装し、選択された
日付がサポートされている各形式でどのようにフォーマットされるかを示す表を表示します。
"""

import logging
from datetime import datetime

from lsprotocol import types

from pygls.cli import start_server
from pygls.lsp.server import LanguageServer

DATE_FORMATS = [
    "%H:%M:%S",
    "%d/%m/%y",
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
]
server = LanguageServer("hover-server", "v1")


@server.feature(types.TEXT_DOCUMENT_HOVER)
def hover(ls: LanguageServer, params: types.HoverParams):
    pos = params.position
    document_uri = params.text_document.uri
    document = ls.workspace.get_text_document(document_uri)

    try:
        line = document.lines[pos.line]
    except IndexError:
        return None

    for fmt in DATE_FORMATS:
        try:
            value = datetime.strptime(line.strip(), fmt)
            break
        except ValueError:
            pass

    else:
        # No valid datetime found.
        return None

    hover_content = [
        f"# {value.strftime('%a %d %b %Y')}",
        "",
        "| Format | Value |",
        "|:-|-:|",
        *[f"| `{fmt}` | {value.strftime(fmt)} |" for fmt in DATE_FORMATS],
    ]

    return types.Hover(
        contents=types.MarkupContent(
            kind=types.MarkupKind.Markdown,
            value="\n".join(hover_content),
        ),
        range=types.Range(
            start=types.Position(line=pos.line, character=0),
            end=types.Position(line=pos.line + 1, character=0),
        ),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    start_server(server)
