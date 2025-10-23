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
"""これは、診断情報の公開モデルを実装します。

LSPにおける診断情報の元祖であり、最も広くサポートされているモデルである公開モデルでは、
サーバーは準備ができたらいつでもクライアントに更新情報を送信できます。
ただし、プッシュモデルとは異なり、クライアントがサーバーにどのドキュメントの診断情報を
計算するかの優先順位付けを支援する方法はありません。

このサーバーは、ドキュメントをスキャンして合計（例：「1 + 2 = 3」）を探し、
不足している答え（警告）または間違っている答え（エラー）を強調表示します。
"""

import logging
import re

from lsprotocol import types

from pygls.cli import start_server
from pygls.lsp.server import LanguageServer
from pygls.workspace import TextDocument

ADDITION = re.compile(r"^\s*(\d+)\s*\+\s*(\d+)\s*=\s*(\d+)?$")


class PublishDiagnosticServer(LanguageServer):
    """「プッシュ モデル」診断を示す言語サーバー。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.diagnostics = {}

    def parse(self, document: TextDocument):
        diagnostics = []

        for idx, line in enumerate(document.lines):
            match = ADDITION.match(line)
            if match is not None:
                left = int(match.group(1))
                right = int(match.group(2))

                expected_answer = left + right
                actual_answer = match.group(3)

                if actual_answer is not None and expected_answer == int(actual_answer):
                    continue

                if actual_answer is None:
                    message = "Missing answer"
                    severity = types.DiagnosticSeverity.Warning
                else:
                    message = f"Incorrect answer: {actual_answer}"
                    severity = types.DiagnosticSeverity.Error

                diagnostics.append(
                    types.Diagnostic(
                        message=message,
                        severity=severity,
                        range=types.Range(
                            start=types.Position(line=idx, character=0),
                            end=types.Position(line=idx, character=len(line) - 1),
                        ),
                    )
                )

        self.diagnostics[document.uri] = (document.version, diagnostics)
        # logging.info("%s", self.diagnostics)


server = PublishDiagnosticServer("diagnostic-server", "v1")


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(ls: PublishDiagnosticServer, params: types.DidOpenTextDocumentParams):
    """各ドキュメントを開いたときに解析する"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc)

    for uri, (version, diagnostics) in ls.diagnostics.items():
        ls.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(
                uri=uri,
                version=version,
                diagnostics=diagnostics,
            )
        )


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls: PublishDiagnosticServer, params: types.DidOpenTextDocumentParams):
    """変更されたドキュメントを解析する"""
    doc = ls.workspace.get_text_document(params.text_document.uri)
    ls.parse(doc)

    for uri, (version, diagnostics) in ls.diagnostics.items():
        ls.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(
                uri=uri,
                version=version,
                diagnostics=diagnostics,
            )
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    start_server(server)
