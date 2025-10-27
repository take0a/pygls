/* -------------------------------------------------------------------------
 * Original work Copyright (c) Microsoft Corporation. All rights reserved.
 * Original work licensed under the MIT License.
 * See ThirdPartyNotices.txt in the project root for license information.
 * All modifications Copyright (c) Open Law Library. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License")
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http: // www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * ----------------------------------------------------------------------- */
"use strict";

import * as net from "net";
import * as path from "path";
import * as vscode from "vscode";
import * as semver from "semver";

import { PythonExtension } from "@vscode/python-extension";
import { LanguageClient, LanguageClientOptions, ServerOptions, State, integer } from "vscode-languageclient/node";

const MIN_PYTHON = semver.parse("3.9.0")

// 他にあれば便利なもの。
// TODO: 選択した env が pygls の要件を満たしているかどうかを確認します。
//       満たしていない場合は、select env コマンドの実行を提案します。
// TODO: TCP Transport
// TODO: WS Transport
// TODO: Web Extension support (requires WASM-WASI!)

let client: LanguageClient;
let clientStarting = false
let python: PythonExtension;
let logger: vscode.LogOutputChannel

/**
 * これはメインのエントリポイントです。
 * vscodeが拡張機能を最初にアクティブ化するときに呼び出されます。
 */
export async function activate(context: vscode.ExtensionContext) {
    logger = vscode.window.createOutputChannel('pygls', { log: true })
    logger.info("Extension activated.")

    await getPythonExtension();
    if (!python) {
        return
    }

    // 言語サーバーを再起動するコマンド
    context.subscriptions.push(
        vscode.commands.registerCommand("pygls.server.restart", async () => {
            logger.info('restarting server...')
            await startLangServer()
        })
    )

    // コマンドを実行...コマンド
    context.subscriptions.push(
        vscode.commands.registerCommand("pygls.server.executeCommand", async () => {
            await executeServerCommand()
        })
    )

    // ユーザーが Python 環境を切り替えた場合は、言語サーバーを再起動します...
    context.subscriptions.push(
        python.environments.onDidChangeActiveEnvironmentPath(async () => {
            logger.info('python env modified, restarting server...')
            await startLangServer()
        })
    )

    // ...または関連する設定オプションを変更した場合
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(async (event) => {
            if (event.affectsConfiguration("pygls.server") || event.affectsConfiguration("pygls.client")) {
                logger.info('config modified, restarting server...')
                await startLangServer()
            }
        })
    )

    // ユーザーが最初のテキスト ドキュメントを開いたら、言語サーバーを起動します...
    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument(
            async () => {
                if (!client) {
                    await startLangServer()
                }
            }
        )
    )

    // ...またはノートブック。
    context.subscriptions.push(
        vscode.workspace.onDidOpenNotebookDocument(
            async () => {
                if (!client) {
                    await startLangServer()
                }
            }
        )
    )

    // ユーザーが変更した場合はサーバーを再起動します。
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(async (document: vscode.TextDocument) => {
            const expectedUri = vscode.Uri.file(path.join(getCwd(), getServerPath()))

            if (expectedUri.toString() === document.uri.toString()) {
                logger.info('server modified, restarting...')
                await startLangServer()
            }
        })
    )
}

export function deactivate(): Thenable<void> {
    return stopLangServer()
}

/**
 * 言語サーバーを起動 (または再起動) します。
 * パラメータだったものを内部で設定から取得するように変えた？
 *
 * @param command 実行する実行ファイル
 * @param args  実行ファイルに渡す引数
 * @param cwd 実行ファイルを実行する作業ディレクトリ
 * @returns
 */
async function startLangServer() {

    // すでにサーバーの起動処理が行われている場合には干渉しないでください。
    if (clientStarting) {
        return
    }

    clientStarting = true
    if (client) {
        await stopLangServer()
    }
    const config = vscode.workspace.getConfiguration("pygls.server")
    const cwd = getCwd()
    const serverPath = getServerPath()

    logger.info(`cwd: '${cwd}'`)
    logger.info(`server: '${serverPath}'`)

    const resource = vscode.Uri.joinPath(vscode.Uri.file(cwd), serverPath)
    const pythonCommand = await getPythonCommand(resource)
    if (!pythonCommand) {
        clientStarting = false
        return
    }

    logger.debug(`python: ${pythonCommand.join(" ")}`)
    const serverOptions: ServerOptions = {
        command: pythonCommand[0],
        args: [...pythonCommand.slice(1), serverPath],
        options: { cwd },
    };

    client = new LanguageClient('pygls', serverOptions, getClientOptions());
    const promises = [client.start()]

    if (config.get<boolean>("debug")) {
        promises.push(startDebugging())
    }

    const results = await Promise.allSettled(promises)
    clientStarting = false

    for (const result of results) {
        if (result.status === "rejected") {
            logger.error(`There was a error starting the server: ${result.reason}`)
        }
    }
}

async function stopLangServer(): Promise<void> {
    if (!client) {
        return
    }

    if (client.state === State.Running) {
        await client.stop()
    }

    client.dispose()
    client = undefined
}

function startDebugging(): Promise<void> {
    if (!vscode.workspace.workspaceFolders) {
        logger.error("Unable to start debugging, there is no workspace.")
        return Promise.reject("Unable to start debugging, there is no workspace.")
    }
    // TODO: デバッグ アダプターの準備ができていることを確認するためのより信頼性の高い方法はありますか?
    setTimeout(async () => {
        await vscode.debug.startDebugging(vscode.workspace.workspaceFolders[0], "pygls: Debug Server")
    }, 2000)
}

function getClientOptions(): LanguageClientOptions {
    const config = vscode.workspace.getConfiguration('pygls.client')
    const options = {
        documentSelector: config.get<any>('documentSelector'),
        outputChannel: logger,
        connectionOptions: {
            maxRestartCount: 0 // サーバー障害時には再起動しないでください。
        },
    };
    logger.info(`client options: ${JSON.stringify(options, undefined, 2)}`)
    return options
}

function startLangServerTCP(addr: number): LanguageClient {
    const serverOptions: ServerOptions = () => {
        return new Promise((resolve /*, reject */) => {
            const clientSocket = new net.Socket();
            clientSocket.connect(addr, "127.0.0.1", () => {
                resolve({
                    reader: clientSocket,
                    writer: clientSocket,
                });
            });
        });
    };

    return new LanguageClient(
        `tcp lang server (port ${addr})`,
        serverOptions,
        getClientOptions()
    );
}

/**
 * 言語サーバーによって提供されたコマンドを実行します。
 */
async function executeServerCommand() {
    if (!client || client.state !== State.Running) {
        await vscode.window.showErrorMessage("There is no language server running.")
        return
    }

    const knownCommands = client.initializeResult.capabilities.executeCommandProvider?.commands
    if (!knownCommands || knownCommands.length === 0) {
        const info = client.initializeResult.serverInfo
        const name = info?.name || "Server"
        const version = info?.version || ""

        await vscode.window.showInformationMessage(`${name} ${version} does not implement any commands.`)
        return
    }

    const commandName = await vscode.window.showQuickPick(knownCommands, { canPickMany: false })
    if (!commandName) {
        return
    }
    logger.info(`executing command: '${commandName}'`)

    const result = await vscode.commands.executeCommand(commandName /* コマンドが引数を受け入れる場合は、ここで渡すことができます */)
    logger.info(`${commandName} result: ${JSON.stringify(result, undefined, 2)}`)
}

/**
 *
 * @returns サーバーを起動する作業ディレクトリ
 */
function getCwd(): string {
    const config = vscode.workspace.getConfiguration("pygls.server")
    let cwd = config.get<string>('cwd')
    if (!cwd) {
        const message = "Please set a working directory via the `pygls.server.cwd` setting"
        logger.error(message)
        throw new Error(message)
    }

    // ${workspaceFolder} などを確認します。
    const match = cwd.match(/^\${(\w+)}/)
    if (match && (match[1] === 'workspaceFolder' || match[1] === 'workspaceRoot')) {
        if (!vscode.workspace.workspaceFolders) {
            const message = "The 'pygls-playground' extension requires an open workspace"
            logger.error(message)
            throw new Error(message)
        }

        // 単一のワークスペースを想定します...
        const workspaceFolder = vscode.workspace.workspaceFolders[0].uri.fsPath
        cwd = cwd.replace(match[0], workspaceFolder)
    }

    return cwd
}

/**
 *
 * @returns サーバーを実装する Python スクリプト。
 */
function getServerPath(): string {
    const config = vscode.workspace.getConfiguration("pygls.server")
    const server = config.get<string>('launchScript')
    return server
}

/**
 * サーバーの起動時に使用する Python コマンドを返します。
 *
 * デバッグが有効になっている場合は、サーバーをデバッグアダプタでラップするために必要な引数も含まれます。
 *
 * @returns サーバーを起動するために必要な完全な Python コマンド。
 */
async function getPythonCommand(resource?: vscode.Uri): Promise<string[] | undefined> {
    const config = vscode.workspace.getConfiguration("pygls.server", resource)
    const pythonCommand = await getPythonInterpreterCmd(resource)
    if (!pythonCommand) {
        return
    }
    const enableDebugger = config.get<boolean>('debug')

    if (!enableDebugger) {
        return pythonCommand
    }

    const debugHost = config.get<string>('debugHost')
    const debugPort = config.get<integer>('debugPort')
    try {
        const debugArgs = await python.debug.getRemoteLauncherCommand(debugHost, debugPort, true)
        // Debugpy recommends we disable frozen modules
        pythonCommand.push("-Xfrozen_modules=off", ...debugArgs)
    } catch (err) {
        logger.error(`Unable to get debugger command: ${err}`)
        logger.error("Debugger will not be available.")
    }

    return pythonCommand
}

/**
 * Pythonインタープリタを起動するために使用するコマンドを返します
 *
 * コマンドが設定されていない場合は、公式の Python 拡張機能を使用して、
 * ユーザーの現在設定されている環境を取得します。
 *
 * @returns Pythonインタープリタを起動するために必要なコマンド
 */
async function getPythonInterpreterCmd(resource?: vscode.Uri): Promise<string[] | undefined> {
    const config = vscode.workspace.getConfiguration("pygls.server", resource)
    const pythonCommand = config.get<string[]>('pythonCommand')
    if (pythonCommand) {
        logger.info(`Using user configured python command: '${pythonCommand}'`)
        return pythonCommand
    }

    if (!python) {
        return
    }

    if (resource) {
        logger.info(`Looking for environment in which to execute: '${resource.toString()}'`)
    }
    // ユーザーが設定した Python インタープリターを使用します。
    const activeEnvPath = python.environments.getActiveEnvironmentPath(resource)
    logger.info(`Found environment: ${activeEnvPath.id}: ${activeEnvPath.path}`)

    const activeEnv = await python.environments.resolveEnvironment(activeEnvPath)
    if (!activeEnv) {
        logger.error(`Unable to resolve envrionment: ${activeEnvPath}`)
        return
    }

    const v = activeEnv.version
    const pythonVersion = semver.parse(`${v.major}.${v.minor}.${v.micro}`)

    // 環境が最小 Python バージョンを満たしているかどうかを確認します。
    if (semver.lt(pythonVersion, MIN_PYTHON)) {
        const message = [
            `Your currently configured environment provides Python v${pythonVersion} `,
            `but pygls requires v${MIN_PYTHON}.\n\nPlease choose another environment.`
        ].join('')

        const response = await vscode.window.showErrorMessage(message, "Change Environment")
        if (!response) {
            return
        } else {
            await vscode.commands.executeCommand('python.setInterpreter')
            return
        }
    }

    const pythonUri = activeEnv.executable.uri
    if (!pythonUri) {
        logger.error(`URI of Python executable is undefined!`)
        return
    }

    return [pythonUri.fsPath]
}

async function getPythonExtension() {
    try {
        python = await PythonExtension.api();
    } catch (err) {
        logger.error(`Unable to load python extension: ${err}`)
    }
}
