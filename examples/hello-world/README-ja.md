# Hello World Pygls Language Server

これはPyglsベースの言語サーバーの最低限の動作例です。メインのREADMEに記載されているものと同じで、`hello.`を「world」と「friend」のオプションで自動補完します。

システムにPyglsがインストールされている必要があります。例：`pip install pygls`。通常は、[venv](https://docs.python.org/3/library/venv.html)、[uv](https://docs.astral.sh/uv/getting-started/installation)などを使用して、`pygls`を言語サーバーの依存関係として正式に定義する必要があります。

# エディター設定

<詳細>
<概要>Neovim Lua (`lspconfig` を使用しない標準の Neovim)</概要>

通常、独自の言語サーバーが完成したら、[LSP Config](https://github.com/neovim/nvim-lspconfig) リポジトリに提出します。これは、Neovim エコシステムで言語サーバーをサポートするためのデファクトスタンダードな方法です。ただし、それまでは、次のようなものを使用することもできます。

  ```lua
  vim.api.nvim_create_autocmd({ "BufEnter" }, {
    -- NB: You must remember to manually put the file extension pattern matchers for each LSP filetype
    pattern = { "*" },
    callback = function()
      vim.lsp.start({
        name = "hello-world-pygls-example",
        cmd = { "python path-to-hello-world-example/main.py" },
        root_dir = vim.fs.dirname(vim.fs.find({ ".git" }, { upward = true })[1])
      })
    end,
  })
  ```
</details>

<details>
<summary>Vim (`vim-lsp`)</summary>

  ```vim
  augroup HelloWorldPythonExample
  au!
  autocmd User lsp_setup call lsp#register_server({
      \ 'name': 'hello-world-pygls-example',
      \ 'cmd': {server_info->['python', 'path-to-hello-world-example/main.py']},
      \ 'allowlist': ['*']
      \ })
  augroup END
  ```
</details>

<details>
<summary>Emacs (`lsp-mode`)</summary>
  通常、言語サーバーが完成したら、[M-x Eglot](https://github.com/joaotavora/eglot) プロジェクトに提出します。すると、自動的にサーバーがセットアップされます。それまでは、以下のツールをご利用ください。

  ```
  (make-lsp-client :new-connection
  (lsp-stdio-connection
    `(,(executable-find "python") "path-to-hello-world-example/main.py"))
    :activation-fn (lsp-activate-on "*")
    :server-id 'hello-world-pygls-example')))
  ```
</details>

<details>
<summary>Sublime</summary>


  ```
  {
      "clients": {
        "pygls-hello-world-example": {
          "command": ["python", "path-to-hello-world-example/main.py"],
          "enabled": true,
          "selector": "source.python"
        }
      }
    }
  ```
</details>

<details>
<summary>VSCode</summary>
  
  VSCodeは設定が最も複雑なエディタです。設定方法については、[json-vscode-extension](https://github.com/openlawlibrary/pygls/tree/master/examples/json-vscode-extension)をご覧ください。
</details>
