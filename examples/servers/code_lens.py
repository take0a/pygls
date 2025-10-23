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
"""これは :lsp:`textDocument/codeLens` および :lsp:`codeLens/resolve` リクエストを実装します。

`VSCode <https://code.visualstudio.com/blogs/2017/02/12/code-lens-roundup>`__ では、
コードレンズはドキュメント内の実際のコード行の上に「ゴーストテキスト」として表示されます。
これらのレンズは通常、コンテキスト情報（参照数など）を表示したり、コマンド（このテストを
実行など）への簡単なアクセスを提供したりするために使用されます。

このサーバーはドキュメントをスキャンして不完全な合計（例: ``1 + 1 =``）を探し、
コードレンズオブジェクトを返します。このオブジェクトをクリックすると、``codeLens.evaluateSum`` 
コマンドが呼び出され、答えが入力されます。
コード レンズの ``command`` フィールドを事前に簡単に計算することもできますが、この例では 
``codeLens/resolve`` を使用して、この計算を実際に必要になるまで延期する方法を示しています。
"""

import logging
import re

import attrs
from lsprotocol import types

from pygls.cli import start_server
from pygls.lsp.server import LanguageServer

ADDITION = re.compile(r"^\s*(\d+)\s*\+\s*(\d+)\s*=(?=\s*$)")
server = LanguageServer("code-lens-server", "v1")


@server.feature(types.TEXT_DOCUMENT_CODE_LENS)
def code_lens(params: types.CodeLensParams):
    """指定されたドキュメントに挿入するコードレンズのリストを返します。

    このメソッドはドキュメント全体を読み取り、ドキュメント内の各要素を識別し、
    各位置にコードレンズを挿入するように言語クライアントに指示します。
    """
    items = []
    document_uri = params.text_document.uri
    document = server.workspace.get_text_document(document_uri)

    lines = document.lines
    for idx, line in enumerate(lines):
        match = ADDITION.match(line)
        if match is not None:
            range_ = types.Range(
                start=types.Position(line=idx, character=0),
                end=types.Position(line=idx, character=len(line) - 1),
            )

            left = int(match.group(1))
            right = int(match.group(2))

            code_lens = types.CodeLens(
                range=range_,
                data={
                    "left": left,
                    "right": right,
                    "uri": document_uri,
                },
            )
            items.append(code_lens)

    return items


@attrs.define
class EvaluateSumArgs:
    """``codeLens.evaluateSum`` コマンドに渡す引数を表します"""

    uri: str
    """編集するドキュメントのURI"""

    left: int
    """``+`` の左引数"""

    right: int
    """``+`` の右引数"""

    line: int
    """編集する行番号"""


@server.feature(types.CODE_LENS_RESOLVE)
def code_lens_resolve(ls: LanguageServer, item: types.CodeLens):
    """指定されたコードレンズの ``command`` フィールドを解決します。

    上記の関数で作成されたコードレンズアイテムにアタッチされた ``data`` を
    使用して、以下の ``evaluateSum`` コマンドの呼び出しを準備します。
    """
    logging.info("Resolving code lens: %s", item)

    left = item.data["left"] if item.data else 0
    right = item.data["right"] if item.data else 0
    uri = item.data["uri"] if item.data else ""

    args = EvaluateSumArgs(
        uri=uri,
        left=left,
        right=right,
        line=item.range.start.line,
    )

    item.command = types.Command(
        title=f"Evaluate {left} + {right}",
        command="codeLens.evaluateSum",
        arguments=[args],
    )
    return item


@server.command("codeLens.evaluateSum")
def evaluate_sum(ls: LanguageServer, args: EvaluateSumArgs):
    logging.info("arguments: %s", args)

    document = ls.workspace.get_text_document(args.uri)
    line = document.lines[args.line]

    # 結果に基づいてドキュメントを更新する編集を計算します。
    answer = args.left + args.right
    edit = types.TextDocumentEdit(
        text_document=types.OptionalVersionedTextDocumentIdentifier(
            uri=args.uri,
            version=document.version,
        ),
        edits=[
            types.TextEdit(
                new_text=f"{line.strip()} {answer}\n",
                range=types.Range(
                    start=types.Position(line=args.line, character=0),
                    end=types.Position(line=args.line + 1, character=0),
                ),
            )
        ],
    )

    # 編集を適用します。
    ls.workspace_apply_edit(
        types.ApplyWorkspaceEditParams(
            edit=types.WorkspaceEdit(document_changes=[edit]),
        ),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    start_server(server)
