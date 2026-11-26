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
    function getWorkspace(folderUri) {
        const folder = folderUri
            ? vscode.workspace.getWorkspaceFolder(folderUri)
            : vscode.workspace.workspaceFolders?.[0];
        if (!folder) {
            void vscode.window.showErrorMessage("Open the bots workspace folder first.");
            return null;
        }
        return folder;
    }

    function runLauncher(folder, launcherName) {
        const launcher = path.join(folder.uri.fsPath, launcherName);
        if (!fs.existsSync(launcher)) {
            void vscode.window.showErrorMessage(`Launcher not found: ${launcher}`);
            return Promise.reject(new Error(`Launcher not found: ${launcher}`));
        }
        return new Promise((resolve, reject) => {
            execFile("bash", [launcher], { cwd: folder.uri.fsPath, encoding: "utf8" }, (error, stdout, stderr) => {
                if (error) {
                    const detail = (stderr || error.message).trim();
                    reject(new Error(detail));
                    return;
                }
                resolve(stdout.trim());
            });
        });
    }

    async function openDashboard() {
        const dashboardUri = await vscode.env.asExternalUri(vscode.Uri.parse("http://127.0.0.1:8000"));
        await vscode.env.openExternal(dashboardUri);
    }

    const startBots = vscode.commands.registerCommand("algotrading.startBots", async (uri) => {
        const folder = getWorkspace(uri);
        if (!folder) return;
        try {
            const output = await runLauncher(folder, "run_bots_tmux.sh");
            attachToBots(folder);
            await openDashboard();
            void vscode.window.showInformationMessage(output || "Started the bots and dashboard.");
        } catch (error) {
            void vscode.window.showErrorMessage(`Could not start the trading stack: ${error.message}`);
        }
    });

    const startDashboard = vscode.commands.registerCommand("algotrading.startDashboard", async (uri) => {
        const folder = getWorkspace(uri);
        if (!folder) return;
        try {
            const output = await runLauncher(folder, "run_dashboard_tmux.sh");
            await openDashboard();
            void vscode.window.showInformationMessage(output || "Started the dashboard.");
        } catch (error) {
            void vscode.window.showErrorMessage(`Could not start the dashboard: ${error.message}`);
        }
    });

    const startTradingStack = vscode.commands.registerCommand("algotrading.startTradingStack", async (uri) => {
        const folder = getWorkspace(uri);
        if (!folder) return;
        try {
            await runLauncher(folder, "run_dashboard_tmux.sh");
            const output = await runLauncher(folder, "run_bots_tmux.sh");
            attachToBots(folder);
            await openDashboard();
            void vscode.window.showInformationMessage(output || "Started bots and dashboard.");
        } catch (error) {
            void vscode.window.showErrorMessage(`Could not start the trading stack: ${error.message}`);
        }
    });

    context.subscriptions.push(startBots, startDashboard, startTradingStack);
}

function deactivate() {}

module.exports = { activate, deactivate };
