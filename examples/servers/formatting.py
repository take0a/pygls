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
"""これは、仕様書に記載されている様々な書式設定リクエストを実装します。

- :lsp:`textDocument/formatting`: ドキュメント全体を書式設定します。
- :lsp:`textDocument/rangeFormatting`: ドキュメント内の指定範囲のみを書式設定します。
- :lsp:`textDocument/onTypeFormatting`: ユーザーが入力中にドキュメントを書式設定します。

これらのメソッドは通常、ユーザーがエディターにドキュメントの書式設定を要求したとき、
または自動トリガー（例：保存時の書式設定）の一部としてクライアントによって呼び出されます。

クライアントによっては、これらのメソッドの一部を有効にするためにユーザーが追加の設定を
行う必要がある場合があります。例えば、VSCode で ``editor.formatOnType`` を設定して 
``textDocument/onTypeFormatting`` を有効にするなどです。

このサーバーは、Markdown スタイルの表の基本的な書式設定を実装しています。

この実装には多少のバグがあり、結果の表が期待どおりにならない場合があります（修正を歓迎します！）が、
クライアントとサーバー間の期待されるやり取りを示すには十分でしょう。
"""

import logging
from typing import Dict
from typing import List
from typing import Optional

import attrs
from lsprotocol import types

from pygls.cli import start_server
from pygls.lsp.server import LanguageServer
from pygls.workspace import TextDocument


@attrs.define
class Row:
    """表内の行を表します"""

    cells: List[str]
    cell_widths: List[int]
    line_number: int


server = LanguageServer("formatting-server", "v1")


@server.feature(types.TEXT_DOCUMENT_FORMATTING)
def format_document(ls: LanguageServer, params: types.DocumentFormattingParams):
    """文書全体の書式を設定する"""
    logging.debug("%s", params)

    doc = ls.workspace.get_text_document(params.text_document.uri)
    rows = parse_document(doc)
    return format_table(rows)


@server.feature(types.TEXT_DOCUMENT_RANGE_FORMATTING)
def format_range(ls: LanguageServer, params: types.DocumentRangeFormattingParams):
    """ドキュメント内の指定された範囲をフォーマットする"""
    logging.debug("%s", params)

    doc = ls.workspace.get_text_document(params.text_document.uri)
    rows = parse_document(doc, params.range)
    return format_table(rows, params.range)


@server.feature(
    types.TEXT_DOCUMENT_ON_TYPE_FORMATTING,
    types.DocumentOnTypeFormattingOptions(first_trigger_character="|"),
)
def format_on_type(ls: LanguageServer, params: types.DocumentOnTypeFormattingParams):
    """ユーザーが入力している間に文書をフォーマットする"""
    logging.debug("%s", params)

    doc = ls.workspace.get_text_document(params.text_document.uri)
    rows = parse_document(doc)
    return format_table(rows)


def format_table(
    rows: List[Row], range_: Optional[types.Range] = None
) -> List[types.TextEdit]:
    """指定された表をフォーマットし、ドキュメントに加える編集のリストを返します。

    範囲が指定された場合、このメソッドは指定された範囲内のドキュメントのみを変更します。
    """
    edits: List[types.TextEdit] = []

    # 最大幅を決定する
    columns: Dict[int, int] = {}
    for row in rows:
        for idx, cell in enumerate(row.cells):
            columns[idx] = max(len(cell), columns.get(idx, 0))

    # 表をフォーマットします。
    cell_padding = 2
    for row in rows:
        # 指定された範囲内の行のみを処理します。
        if skip_line(row.line_number, range_):
            continue

        if len(row.cells) == 0:
            # 行にセルがない場合、これは区切り行である必要があります。
            cells: List[str] = []
            empty_cells = [
                "-" * (columns[i] + cell_padding) for i in range(len(columns))
            ]
        else:
            # それ以外の場合は、各行のセルの数が一定であることを確認してください。
            empty_cells = [" " for _ in range(len(columns) - len(row.cells))]
            cells = [
                c.center(columns[i] + cell_padding) for i, c in enumerate(row.cells)
            ]

        line = f"|{'|'.join([*cells, *empty_cells])}|\n"
        edits.append(
            types.TextEdit(
                range=types.Range(
                    start=types.Position(line=row.line_number, character=0),
                    end=types.Position(line=row.line_number + 1, character=0),
                ),
                new_text=line,
            )
        )

    return edits


def parse_document(
    document: TextDocument, range_: Optional[types.Range] = None
) -> List[Row]:
    """指定されたドキュメントをテーブル行のリストに解析します。

    range_ が指定されている場合は、テーブルの範囲内の行のみを考慮します。
    """
    rows: List[Row] = []
    for linum, line in enumerate(document.lines):
        if skip_line(linum, range_):
            continue

        line = line.strip()
        cells = [c.strip() for c in line.split("|")]

        if line.startswith("|"):
            cells.pop(0)

        if line.endswith("|"):
            cells.pop(-1)

        chars = set()
        for c in cells:
            chars.update(set(c))

        logging.debug("%s: %s", chars, cells)

        if chars == {"-"}:
            # 区切り行をチェックし、空のリストを使用してそれを表します。
            cells = []

        elif len(cells) == 0:
            continue

        row = Row(cells=cells, line_number=linum, cell_widths=[len(c) for c in cells])

        logging.debug("%s", row)
        rows.append(row)

    return rows


def skip_line(line: int, range_: Optional[types.Range]) -> bool:
    """範囲を指定すると、指定された行番号をスキップするかどうかを決定します。"""

    if range_ is None:
        return False

    return any([line < range_.start.line, line > range_.end.line])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    start_server(server)
