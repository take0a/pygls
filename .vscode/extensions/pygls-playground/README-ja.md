# Pygls Playground

![pygls-playground 拡張機能の動作スクリーンショット](https://user-images.githubusercontent.com/2675694/260591942-b7001a7b-3081-439d-b702-5f8a489856db.png)

この VSCode 拡張機能は、2つの目的を達成するために開発されました。

- サンプルサーバーを試したり、独自のサーバーを作成したりすることで、pygls フレームワークを簡単に試せる環境を提供すること。

- pygls ベースの言語サーバーを VSCode に統合するために必要な最小限のサンプルを提供すること。

より完全な VSCode クライアントの例については、Python コードを VSCode 拡張機能自体にバンドルする方法の詳細も含まれており、Microsoft の [Python ツールのテンプレート拡張機能](https://github.com/microsoft/vscode-python-tools-extension-template) も参考になるかもしれません。

## セットアップ

### サーバーの依存関係をインストール

リポジトリのルートディレクトリでターミナルを開きます

1. 仮想環境を作成します
   ```
   python -m venv env
   ```

1. 環境をアクティベートする
   ```
   source ./env/bin/activate
   ```

1. `pygls`をインストールする
   ```
   python -m pip install -e .
   ```

### クライアントの依存関係をインストールします

このファイルと同じディレクトリでターミナルを開き、以下のコマンドを実行します。

1. ノードの依存関係をインストールします
   ```
   npm install --no-save
   ```

1. 拡張機能をコンパイルする
   ```
   npm run compile
   ```

   あるいは、拡張機能自体を積極的に操作する場合は、`npm run watch` を実行することもできます。

### 拡張機能の実行 (VSCode v1.89+)

> [!重要]
> VSCode が `pygls-playground` を有効な拡張機能として認識するには、VSCode 内でこのリポジトリを開く **前** に上記の設定手順を完了する必要があります。
> 拡張機能をコンパイルする前に VSCode を開いた場合は、コマンドパレット (Ctrl+Shift+P) から `Developer: Reload Window` コマンドを実行する必要があります。

1. VSCode で `pygls` リポジトリを開きます。

1. 「拡張機能」タブ (Ctrl+Shift+X) に移動し、「*推奨*」セクションで `pygls-playground` 拡張機能を見つけます (マーケットプレイスで検索しないでください)。「ワークスペース拡張機能をインストール」ボタンをクリックします。
   **ボタンに「インストール」としか表示されていない場合は、この拡張機能の適切なバージョンが見つかりません**

1. VSCode が `pygls` がインストールされた仮想環境を使用していることを確認してください。
   `Python: Select Interpreter` コマンドを使用して、適切なインタープリターを選択できます。

または、`.vscode/settings.json` ファイルで `pygls.server.pythonPath` オプションを設定することもできます。

### 拡張機能の実行 (VSCode v1.88 以前)

1. VS Code でこのディレクトリを開きます。

1. プレイグラウンドは、サンプル言語サーバーを実行するための適切な Python 環境を選択するために、[VSCode 用 Python 拡張機能](https://marketplace.visualstudio.com/items?itemName=ms-python.python) を使用します。
   まだインストールしていない場合は、インストールしてウィンドウをリロードしてください。

1. 実行とデバッグビューを開きます (`Ctrl + Shift + D`)。

1. 「クライアントを起動」を選択し、`F5` キーを押すと、`pygls-playground` 拡張機能が有効になった 2 つ目の VSCode ウィンドウが開きます。

1. VSCode が `pygls` がインストールされた仮想環境を使用していることを確認してください。
   `Python: Select Interpreter` コマンドを使用して、適切なインタープリターを選択できます。

あるいは、`.vscode/settings.json` ファイルで `pygls.server.pythonPath` オプションを設定することもできます。

## 設定

デフォルトでは、`pygls-playground` 拡張機能は、このリポジトリの `examples/servers` フォルダにあるサンプルの `code_actions.py` サーバーを実行するように設定されています。
(最適な結果を得るには、`examples/servers/workspace/sums.txt` ファイルを開いてみてください。)

ただし、このリポジトリの `.vscode/settings.json` ファイルを使用して、これやその他の設定を変更できます。

### サーバーの選択

> [!TIP]
> 利用可能なサーバーと、それらに最適なファイルの詳細については、`examples/servers` フォルダ内の [README](../../../examples/servers/README.md) をご覧ください。

別のサンプルサーバーを選択するには、`pygls.server.launchScript` 設定を、実行するサーバーの名前に変更してください。

### 作業ディレクトリの選択

> [!TIP]
> 不可解な「Error: spawn /.../python ENOENT」メッセージは、拡張機能が間違った作業ディレクトリを使用していることが原因であることが多いです。

すべてが期待通りに動作する場合、`pygls-playground` 拡張機能はデフォルトで `examples/servers/` フォルダを作業ディレクトリとして使用するはずです。

そうでない場合、または別のディレクトリに変更したい場合は、`pygls.server.cwd` オプションを変更できます。

### ドキュメントの選択

言語サーバーは通常、比較的少数のファイル形式に特化しているため、クライアントはサーバーにドキュメントについてのみ問い合わせます。

`code_actions.py` の例は、`plaintext` ファイル（例：提供されている `sums.txt` ファイル）で使用することを目的としています。異なるファイル形式に対応するサーバーを使用するには、`pygls.client.documentSelector` オプションを変更します。

例えば、`json` ファイルに対応するサーバーを使用する場合は、以下のコマンドを実行します。

```
"pygls.client.documentSelector": [
    {
        "scheme": "file",
        "language": "json"
    },
],
```

既知の言語識別子の完全なリストは、[こちら](https://code.visualstudio.com/docs/languages/identifiers#_known-language-identifiers) でご覧いただけます。

`pygls.client.documentSelector` オプションに渡すことができるすべてのオプションの詳細については、[LSP 仕様](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#documentFilter) をご覧ください。

### サーバーのデバッグ

言語サーバーをデバッグするには、`pygls.server.debug` オプションを `true` に設定します。
サーバーが再起動し、デバッガーが自動的に接続されます。

デバッガーが使用するホストとポートは、`pygls.server.debugHost` オプションと `pygls.server.debugPort` オプションで制御できます。