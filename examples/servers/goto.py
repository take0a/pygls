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
"""これは、仕様書に記載されている様々な Goto "X" リクエストを実装します。

- :lsp:`textDocument/definition`
- :lsp:`textDocument/declaration`
- :lsp:`textDocument/implementation`
- :lsp:`textDocument/typeDefinition`

:lsp:`textDocument/references` リクエストも同様です。

ご覧のとおり、これらのメソッドはすべて本質的に同じです。ドキュメント URI を受け取り、
0 個以上の場所を返します（goto definition でも複数の結果が返されることがあります）。
これらのメソッドの唯一の違いは、ターゲット言語における定義と宣言の意味の違いです。

つまり、以下のサンプルサーバーが返す結果の選択は完全に任意です。
"""

import logging
import re

from lsprotocol import types

from pygls.cli import start_server
from pygls.lsp.server import LanguageServer
from pygls.workspace import TextDocument

ARGUMENT = re.compile(r"(?P<name>\w+): (?P<type>\w+)")
FUNCTION = re.compile(r"^fn ([a-z]\w+)\(")
TYPE = re.compile(r"^type ([A-Z]\w+)\(")


class GotoLanguageServer(LanguageServer):
    """LSP 仕様のさまざまな「Goto X」メソッドをデモンストレーションする言語サーバー。
    """

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


server = GotoLanguageServer("goto-server", "v1")


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: GotoLanguageServer, params: types.DidOpenTextDocumentParams):
    """各ドキュメントを開いたときに解析する"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: GotoLanguageServer, params: types.DidOpenTextDocumentParams):
    """変更されたドキュメントを解析する"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc)


@server.feature(types.TEXT_DOCUMENT_TYPE_DEFINITION)
def goto_type_definition(ls: GotoLanguageServer, params: types.TypeDefinitionParams):
    """オブジェクトの型定義にジャンプします。"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    index = ls.index.get(doc.uri)
    if index is None:
        return

    try:
        line = doc.lines[params.position.line]
    except IndexError:
        line = ""

    word = doc.word_at_position(params.position)

    for match in ARGUMENT.finditer(line):
        if match.group("name") == word:
            if (range_ := index["types"].get(match.group("type"), None)) is not None:
                return types.Location(uri=doc.uri, range=range_)


@server.feature(types.TEXT_DOCUMENT_DEFINITION)
def goto_definition(ls: GotoLanguageServer, params: types.DefinitionParams):
    """オブジェクトの定義にジャンプします。"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    index = ls.index.get(doc.uri)
    if index is None:
        return

    word = doc.word_at_position(params.position)

    # Is word a type?
    if (range_ := index["types"].get(word, None)) is not None:
        return types.Location(uri=doc.uri, range=range_)


@server.feature(types.TEXT_DOCUMENT_DECLARATION)
def goto_declaration(ls: GotoLanguageServer, params: types.DeclarationParams):
    """オブジェクトの宣言にジャンプします。"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    index = ls.index.get(doc.uri)
    if index is None:
        return

    try:
        line = doc.lines[params.position.line]
    except IndexError:
        line = ""

    word = doc.word_at_position(params.position)

    for match in ARGUMENT.finditer(line): # parse した結果から見つけるんじゃないのか？
        if match.group("name") == word:
            linum = params.position.line
            return types.Location(
                uri=doc.uri,
                range=types.Range(
                    start=types.Position(line=linum, character=match.start()),
                    end=types.Position(line=linum, character=match.end()),
                ),
            )


@server.feature(types.TEXT_DOCUMENT_IMPLEMENTATION)
def goto_implementation(ls: GotoLanguageServer, params: types.ImplementationParams):
    """オブジェクトの実装にジャンプします。"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    index = ls.index.get(doc.uri)
    if index is None:
        return

    word = doc.word_at_position(params.position)

    # Is word a function?
    if (range_ := index["functions"].get(word, None)) is not None:
        return types.Location(uri=doc.uri, range=range_)


@server.feature(types.TEXT_DOCUMENT_REFERENCES)
def find_references(ls: GotoLanguageServer, params: types.ReferenceParams):
    """オブジェクトの参照を見つけます。"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    index = ls.index.get(doc.uri)
    if index is None:
        return

    word = doc.word_at_position(params.position)
    is_object = any([word in index[name] for name in index])
    if not is_object:
        return

    references = []
    for linum, line in enumerate(doc.lines):
        for match in re.finditer(f"\\b{word}\\b", line):
            references.append(
                types.Location(
                    uri=doc.uri,
                    range=types.Range(
                        start=types.Position(line=linum, character=match.start()),
                        end=types.Position(line=linum, character=match.end()),
                    ),
                )
            )

    return references


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    start_server(server)
