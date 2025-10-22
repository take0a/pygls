# Example Servers

VSCode でこれらを実行する方法については、[ドキュメント](https://pygls.readthedocs.io/en/latest/pygls/howto/use-the-pygls-playground.html#howto-use-pygls-playground) を参照してください。

| ファイル名 | 対応アプリケーション | 説明 |
|-|-|-|
| `code_actions.py` | `sums.txt` | コードアクションで合計を評価 |
| `code_lens.py` | `sums.txt` | コードレンズで合計を評価 |
| `colors.py` | `colors.txt` | サポートされているクライアントでは、色の値の視覚的な表現とカラーピッカーも提供します |
| `formatting.py`| `table.txt`| Markdown のような表に対して、ドキュメント全体、選択範囲のみ、および入力時の書式設定を実装します [^1] [^2] |
| `goto.py` | `code.txt` | 仕様書にあるさまざまな「Goto X」および「Find references」リクエストを実装します |
| `hover.py` | `dates.txt` | カーソルの下の日付を複数の形式で表示するポップアップを開きます |
| `inlay_hints.py` | `sums.txt` | インレイヒントを使用して、ファイル内の数値のバイナリ表現を表示します |
| `links.py` | `links.txt` | `textDocument/documentLink` を実装します |
| `publish_diagnostics.py` | `sums.txt` | 「push-model」診断を使用して、不足している回答または誤った回答を強調表示します |
| `pull_diagnostics.py` | `sums.txt` | 「pull-model」診断を使用して、不足している回答または誤った回答を強調表示します |
| `rename.py` | `code.txt` |シンボル名の変更を実装します |

[^1]: 入力時のフォーマットを有効にするには、`.vscode/settings.json` の `editor.formatOnType` オプションのコメントを解除してください。

[^2]: このサーバーは、これらのメソッドを実装するために必要な最小限の機能を示すには十分です。検討すべき追加オプションについては、`params` オブジェクトの内容を確認してください。
