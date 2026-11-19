const { execFile } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const vscode = require("vscode");

function attachToBots(folder) {
    const terminal = vscode.window.createTerminal({
        name: "Trading Bots (tmux)",
        cwd: folder.uri.fsPath,
    });
    terminal.show(true);
    terminal.sendText("tmux attach -t trading-bots");
}

function activate(context) {
    const command = vscode.commands.registerCommand("algotrading.startBots", (uri) => {
        const folder = uri
            ? vscode.workspace.getWorkspaceFolder(uri)
            : vscode.workspace.workspaceFolders?.[0];

        if (!folder) {
            void vscode.window.showErrorMessage("Open the bots workspace folder first.");
            return;
        }

        const launcher = path.join(folder.uri.fsPath, "run_bots_tmux.sh");
        if (!fs.existsSync(launcher)) {
            void vscode.window.showErrorMessage(`Bot launcher not found: ${launcher}`);
            return;
        }

        execFile("bash", [launcher], { cwd: folder.uri.fsPath, encoding: "utf8" }, (error, stdout, stderr) => {
            if (error) {
                execFile("tmux", ["has-session", "-t", "trading-bots"], (sessionError) => {
                    if (!sessionError) {
                        attachToBots(folder);
                        void vscode.window.showInformationMessage("The bots are already running; attached to their tmux output.");
                        return;
                    }

                    const detail = (stderr || error.message).trim();
                    void vscode.window.showErrorMessage(`Could not start the bots: ${detail}`);
                });
                return;
            }

            attachToBots(folder);
            void vscode.window.showInformationMessage(stdout.trim() || "Started the bots in tmux.");
        });
    });

    context.subscriptions.push(command);
}

function deactivate() {}

module.exports = { activate, deactivate };
