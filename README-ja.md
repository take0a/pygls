[![PyPI Version](https://img.shields.io/pypi/v/pygls.svg)](https://pypi.org/project/pygls/) ![!pyversions](https://img.shields.io/pypi/pyversions/pygls.svg) ![license](https://img.shields.io/pypi/l/pygls.svg) [![Documentation Status](https://img.shields.io/badge/docs-latest-green.svg)](https://pygls.readthedocs.io/en/latest/)

# pygls: 汎用言語サーバーフレームワーク

_pygls_ (「パイグラス」のように発音します) は、[言語サーバープロトコル](https://microsoft.github.io/language-server-protocol/specification) の Python による汎用実装です。わずか数行のコードで独自の [言語サーバー](https://langserver.org/) を作成するための基盤として使用できます。

## クイックスタート

```python
from pygls.lsp.server import LanguageServer
from lsprotocol import types

server = LanguageServer("example-server", "v0.1")

@server.feature(types.TEXT_DOCUMENT_COMPLETION)
def completions(params: types.CompletionParams):
    items = []
    document = server.workspace.get_text_document(params.text_document.uri)
    current_line = document.lines[params.position.line].strip()
    if current_line.endswith("hello."):
        items = [
            types.CompletionItem(label="world"),
            types.CompletionItem(label="friend"),
        ]
    return types.CompletionList(is_incomplete=False, items=items)

server.start_io()
```

エディターで自動補完を有効にすると、次のような表示になるかもしれません。

![補完](https://raw.githubusercontent.com/openlawlibrary/pygls/master/docs/assets/hello-world-completion.png)

## ドキュメントとチュートリアル

完全なドキュメントとチュートリアルは <https://pygls.readthedocs.io/en/latest/> でご覧いただけます。

## _pygls_ ベースのプロジェクト

既知のすべての _pygls_ [実装](https://github.com/take0a/pygls/blob/main/Implementations-ja.md) の一覧表を作成しています。ご自身の実装、または不足していると思われる実装があれば、プルリクエストを送信してください。

## 代替案

_pygls_ の主な代替案は、Microsoft の [NodeJS ベースの汎用言語サーバーフレームワーク](https://github.com/microsoft/vscode-languageserver-node) です。Microsoft 製であるため、VSCode の拡張に重点を置いていますが、理論的にはあらゆるエディターのサポートに使用できます。pygls は VSCode に特化していないため、より多くのエディターをサポートしたい場合は、pygls の方が適している可能性があります。

他にも「汎用」という説明、あるいは少なくとも意図を持つ言語サーバーは存在します。ただし、それらは強力な _configuration_ を備えているという意味でのみ汎用的です。これらの言語サーバーは、プログラミング（_pygls_ の場合）で実現できる汎用性ではなく、設定によって実現できる汎用性を実現しています。
* https://github.com/iamcco/diagnostic-languageserver
* https://github.com/mattn/efm-langserver
* https://github.com/jose-elias-alvarez/null-ls.nvim (Neovim のみ)

## テスト

すべてのPyglsサブタスクには`uv`が必要です: https://docs.astral.sh/uv/getting-started/installation

* `uv run --all-extras poe test`
* `uv run --all-extras poe test-pyodide`


## 貢献

_pygls_ への貢献は大歓迎です❤️ 開始方法については、[貢献](https://github.com/take0a/pygls/blob/main/CONTRIBUTING-ja.md) および [行動規範](https://github.com/take0a/pygls/blob/main/CODE_OF_CONDUCT-ja.md) ドキュメントをご覧ください。

## 寄付

[Open Law Library](http://www.openlawlib.org/) は、501(c)(3) に基づく免税団体です。[スポンサーシップ](https://github.com/sponsors/openlawlibrary) を通じて、オープンソースプロジェクトの維持と、すべての人に法を開示する活動にご協力ください。

### サポーター

下記のサポーターの皆様に心より感謝申し上げます。
* [mpourmpoulis](https://github.com/mpourmpoulis)

## ライセンス

Apache-2.0
