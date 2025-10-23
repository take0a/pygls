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
"""これは、LSP 仕様の :lsp:`textDocument/documentSymbol` リクエストと 
:lsp:`workspace/symbol` リクエストを実装します。

VSCode では、`textDocument/documentSymbol`` リクエストは、`アウトラインビュー 
<https://code.visualstudio.com/docs/getstarted/tips-and-tricks#_outline-view>`__ や
`ファイル内のシンボルへ移動 
<https://code.visualstudio.com/docs/getstarted/tips-and-tricks#_go-to-symbol-in-file>`__ 
のような機能を提供します。
一方、`ワークスペース内のシンボルへ移動 
<https://code.visualstudio.com/docs/getstarted/tips-and-tricks#_go-to-symbol-in-workspace>`__ は、
`workspace/symbol`` リクエストによって実現されます。

サーバーが 2 つのリクエストに対して返す結果は似ていますが、同一ではありません。
主な違いは、「textDocument/documentSymbol」はシンボル階層を提供できるのに対し、
「workspace/symbol」はフラットなリストである点です。

このサーバーは、*pygls* リポジトリのサンプルワークスペースにある「code.txt」で
紹介されている擬似プログラミング言語に対するこれらのリクエストを実装しています。

.. literalinclude:: ../../../../examples/servers/workspace/code.txt
   :language: none
"""

import logging
import re

from lsprotocol import types

from pygls.cli import start_server
from pygls.lsp.server import LanguageServer
from pygls.workspace import TextDocument

ARGUMENT = re.compile(r"(?P<name>\w+)(: ?(?P<type>\w+))?")
FUNCTION = re.compile(r"^fn ([a-z]\w+)\(([^)]*?)\)")
TYPE = re.compile(r"^type ([A-Z]\w+)\(([^)]*?)\)")


class SymbolsLanguageServer(LanguageServer):
    """LSP 仕様のドキュメントおよびワークスペース シンボル メソッドを示す言語サーバー。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = {}

    def parse(self, doc: TextDocument):
        typedefs = {}
        funcs = {}

        for linum, line in enumerate(doc.lines):
            if (match := TYPE.match(line)) is not None:
                self.parse_typedef(typedefs, linum, line, match)

            elif (match := FUNCTION.match(line)) is not None:
                self.parse_function(funcs, linum, line, match)

        self.index[doc.uri] = {
            "types": typedefs,
            "functions": funcs,
        }
        logging.info("Index: %s", self.index)

    def parse_function(self, funcs, linum, line, match):
        """指定された行の関数定義を解析します。"""
        name = match.group(1)
        args = match.group(2)

        start_char = match.start() + line.find(name)
        args_offset = match.start() + line.find(args)

        funcs[name] = dict(
            range_=types.Range(
                start=types.Position(line=linum, character=start_char),
                end=types.Position(line=linum, character=start_char + len(name)),
            ),
            args=self.parse_args(args, linum, args_offset),
        )

    def parse_typedef(self, typedefs, linum, line, match):
        """指定された行の型定義を解析します。"""
        name = match.group(1)
        fields = match.group(2)

        start_char = match.start() + line.find(name)
        field_offset = match.start() + line.find(fields)

        typedefs[name] = dict(
            range_=types.Range(
                start=types.Position(line=linum, character=start_char),
                end=types.Position(line=linum, character=start_char + len(name)),
            ),
            fields=self.parse_args(fields, linum, field_offset),
        )

    def parse_args(self, text: str, linum: int, offset: int):
        """型または関数定義の引数を解析する"""
        arguments = {}

        for match in ARGUMENT.finditer(text):
            name = match.group("name")
            start_char = offset + text.find(name)

            arguments[name] = types.Range(
                start=types.Position(line=linum, character=start_char),
                end=types.Position(line=linum, character=start_char + len(name)),
            )

        return arguments


server = SymbolsLanguageServer("symbols-server", "v1")


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: SymbolsLanguageServer, params: types.DidOpenTextDocumentParams):
    """各ドキュメントを開いたときに解析する"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: SymbolsLanguageServer, params: types.DidOpenTextDocumentParams):
    """変更されたドキュメントを解析する"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc)


@server.feature(types.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(ls: SymbolsLanguageServer, params: types.DocumentSymbolParams):
    """指定されたドキュメントで定義されているすべてのシンボルを返します。"""
    if (index := ls.index.get(params.text_document.uri)) is None:
        return None

    results = []
    for name, info in index.get("types", {}).items():
        range_ = info["range_"]
        type_symbol = types.DocumentSymbol(
            name=name,
            kind=types.SymbolKind.Class,
            range=types.Range(
                start=types.Position(line=range_.start.line, character=0),
                end=types.Position(line=range_.start.line + 1, character=0),
            ),
            selection_range=range_,
            children=[],
        )

        for name, range_ in info["fields"].items():
            field_symbol = types.DocumentSymbol(
                name=name,
                kind=types.SymbolKind.Field,
                range=range_,
                selection_range=range_,
            )
            if isinstance(type_symbol.children, list):
                type_symbol.children.append(field_symbol)

        results.append(type_symbol)

    for name, info in index.get("functions", {}).items():
        range_ = info["range_"]
        func_symbol = types.DocumentSymbol(
            name=name,
            kind=types.SymbolKind.Function,
            range=types.Range(
                start=types.Position(line=range_.start.line, character=0),
                end=types.Position(line=range_.start.line + 1, character=0),
            ),
            selection_range=range_,
            children=[],
        )

        for name, range_ in info["args"].items():
            arg_symbol = types.DocumentSymbol(
                name=name,
                kind=types.SymbolKind.Variable,
                range=range_,
                selection_range=range_,
            )
            if isinstance(func_symbol.children, list):
                func_symbol.children.append(arg_symbol)

        results.append(func_symbol)

    return results


@server.feature(types.WORKSPACE_SYMBOL)
def workspace_symbol(ls: SymbolsLanguageServer, params: types.WorkspaceSymbolParams):
    """ワークスペース内のドキュメントで定義されているすべてのシンボルを返します。"""
    query = params.query
    results = []

    for uri, symbols in ls.index.items():
        for type_name, info in symbols.get("types", {}).items():
            if params.query == "" or type_name.startswith(query):
                func_symbol = types.WorkspaceSymbol(
                    name=type_name,
                    kind=types.SymbolKind.Class,
                    location=types.Location(uri=uri, range=info["range_"]),
                )
                results.append(func_symbol)

            for field_name, range_ in info["fields"].items():
                if params.query == "" or field_name.startswith(query):
                    field_symbol = types.WorkspaceSymbol(
                        name=field_name,
                        kind=types.SymbolKind.Field,
                        location=types.Location(uri=uri, range=range_),
                        container_name=type_name,
                    )
                    results.append(field_symbol)

        for func_name, info in symbols.get("functions", {}).items():
            if params.query == "" or func_name.startswith(query):
                func_symbol = types.WorkspaceSymbol(
                    name=func_name,
                    kind=types.SymbolKind.Function,
                    location=types.Location(uri=uri, range=info["range_"]),
                )
                results.append(func_symbol)

            for arg_name, range_ in info["args"].items():
                if params.query == "" or arg_name.startswith(query):
                    arg_symbol = types.WorkspaceSymbol(
                        name=arg_name,
                        kind=types.SymbolKind.Variable,
                        location=types.Location(uri=uri, range=range_),
                        container_name=func_name,
                    )
                    results.append(arg_symbol)

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    start_server(server)
