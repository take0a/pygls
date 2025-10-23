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
"""これは :lsp:`textDocument/inlayHint` および :lsp:`inlayHint/resolve` 
リクエストを実装します。

VSCode <https://code.visualstudio.com/Docs/editor/editingevolved#_inlay-hints>`__ 
などのエディターでは、インレイヒントは多くの場合、インラインの「ゴーストテキスト」として
レンダリングされます。これらは通常、変数の型や関数の戻り値を示すために使用されます。

このサーバーは ``textDocument/inlayHint`` を実装し、指定されたドキュメント内の整数値を
スキャンし、その数値に相当するバイナリ表現を返します。
インレイヒントのツールチップも同じ方法で簡単に計算できますが、この例では ``inlayHint/resolve`` 
を使用して、高負荷な計算を必要なときに延期する方法を示しています。
"""

import re
from typing import Optional

from lsprotocol import types
from pygls.cli import start_server
from pygls.lsp.server import LanguageServer

NUMBER = re.compile(r"\d+")
server = LanguageServer("inlay-hint-server", "v1")


def parse_int(chars: str) -> Optional[int]:
    try:
        return int(chars)
    except Exception:
        return None


@server.feature(types.TEXT_DOCUMENT_INLAY_HINT)
def inlay_hints(params: types.InlayHintParams):
    items = []
    document_uri = params.text_document.uri
    document = server.workspace.get_text_document(document_uri)

    start_line = params.range.start.line
    end_line = params.range.end.line

    lines = document.lines[start_line : end_line + 1]
    for lineno, line in enumerate(lines):
        for match in NUMBER.finditer(line):
            if not match:
                continue

            number = parse_int(match.group(0))
            if number is None:
                continue

            binary_num = bin(number).split("b")[1]
            items.append(
                types.InlayHint(
                    label=f":{binary_num}",
                    kind=types.InlayHintKind.Type,
                    padding_left=False,
                    padding_right=True,
                    position=types.Position(line=lineno, character=match.end()),
                )
            )

    return items


@server.feature(types.INLAY_HINT_RESOLVE)
def inlay_hint_resolve(hint: types.InlayHint):
    try:
        n = int(str(hint.label)[1:], 2)
        hint.tooltip = f"Binary representation of the number: {n}"
    except Exception:
        pass

    return hint


if __name__ == "__main__":
    start_server(server)
