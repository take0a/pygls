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
"""これは :lsp:`textDocument/rename` と :lsp:`textDocument/prepareRename` を
実装します。

`textDocument/rename` メソッドは、指定されたシンボルのすべての出現を正しく
名前変更するためにクライアントが実行すべき編集のコレクションを返す必要があります。

`textDocument/prepareRename` メソッドは、クライアントが指定されたシンボルの
名前変更が実際に意味のあるものであるかどうかを確認するために使用され、サーバーは
操作を無効として拒否する機会を得ます。

.. 注::

    このサーバーの名前変更の実装は、単純な検索と置換と変わりません。実際のサーバーでは、
    関連するスコープ内のシンボルのみの名前変更を行うことを確認する必要があります。
"""

import logging
import re
from typing import List

from lsprotocol import types

from pygls.cli import start_server
from pygls.lsp.server import LanguageServer
from pygls.workspace import TextDocument

ARGUMENT = re.compile(r"(?P<name>\w+): (?P<type>\w+)")
FUNCTION = re.compile(r"^fn ([a-z]\w+)\(")
TYPE = re.compile(r"^type ([A-Z]\w+)\(")


class RenameLanguageServer(LanguageServer):
    """シンボルの名前変更を示す言語サーバー。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = {}

    def parse(self, doc: TextDocument):
        typedefs = {}
        funcs = {}

        for linum, line in enumerate(doc.lines):
            if (match := TYPE.match(line)) is not None:
                name = match.group(1)
                start_char = match.start() + line.find(name)

                typedefs[name] = types.Range(
                    start=types.Position(line=linum, character=start_char),
                    end=types.Position(line=linum, character=start_char + len(name)),
                )

            elif (match := FUNCTION.match(line)) is not None:
                name = match.group(1)
                start_char = match.start() + line.find(name)

                funcs[name] = types.Range(
                    start=types.Position(line=linum, character=start_char),
                    end=types.Position(line=linum, character=start_char + len(name)),
                )

        self.index[doc.uri] = {
            "types": typedefs,
            "functions": funcs,
        }
        logging.info("Index: %s", self.index)


server = RenameLanguageServer("rename-server", "v1")


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: RenameLanguageServer, params: types.DidOpenTextDocumentParams):
    """各ドキュメントを開いたときに解析する"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: RenameLanguageServer, params: types.DidOpenTextDocumentParams):
    """変更されたドキュメントを解析する"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc)


@server.feature(types.TEXT_DOCUMENT_RENAME)
def rename(ls: RenameLanguageServer, params: types.RenameParams):
    """指定された位置のシンボルの名前を変更します。"""
    logging.debug("%s", params)

    doc = ls.workspace.get_text_document(params.text_document.uri)
    index = ls.index.get(doc.uri)
    if index is None:
        return None

    word = doc.word_at_position(params.position)
    is_object = any([word in index[name] for name in index])
    if not is_object:
        return None

    edits: List[types.TextEdit] = []
    for linum, line in enumerate(doc.lines):
        for match in re.finditer(f"\\b{word}\\b", line):
            edits.append(
                types.TextEdit(
                    new_text=params.new_name,
                    range=types.Range(
                        start=types.Position(line=linum, character=match.start()),
                        end=types.Position(line=linum, character=match.end()),
                    ),
                )
            )

    return types.WorkspaceEdit(changes={params.text_document.uri: edits})


@server.feature(types.TEXT_DOCUMENT_PREPARE_RENAME)
def prepare_rename(ls: RenameLanguageServer, params: types.PrepareRenameParams):
    """指定された場所のシンボルの名前を変更することが有効な操作であるかどうかを
    判断するためにクライアントによって呼び出されます。"""
    logging.debug("%s", params)

    doc = ls.workspace.get_text_document(params.text_document.uri)
    index = ls.index.get(doc.uri)
    if index is None:
        return None

    word = doc.word_at_position(params.position)
    is_object = any([word in index[name] for name in index])
    if not is_object:
        return None

    # この時点で、このシンボルの名前を変更できます。
    #
    # 簡潔にするために、クライアントにデフォルトの動作を使用するように指示することも
    # できますが、これは仕様としては比較的新しいもの（LSP v3.16+）であるため、
    # 本番サーバーではこの方法で応答する前にクライアントの機能を確認する必要があります。
    return types.PrepareRenameDefaultBehavior(default_behavior=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    start_server(server)
