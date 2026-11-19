#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"
SESSION="trading-bots"

if ! command -v tmux >/dev/null 2>&1; then
    printf 'tmux is not installed. Install it with: sudo apt install tmux\n' >&2
    exit 1
fi

if [[ ! -x "$PYTHON" ]]; then
    printf 'Project Python environment not found or not executable: %s\n' "$PYTHON" >&2
    exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
    printf 'tmux session "%s" already exists. Attach with: tmux attach -t %s\n' "$SESSION" "$SESSION" >&2
    exit 1
fi

SCRIPTS=(
    "Fyers/BOT_fyers_nifty_g_pool_vE6.py"
    "Fyers/BOT_fyers_sensex_g_pool_v8_9.py"
    "Rmoney/BOT_rmoney_sensex_g_pool_v8_9.py"
    "Rmoney/BOT_rmoney_nifty_g_pool_vE6.py"
)

for script in "${SCRIPTS[@]}"; do
    if [[ ! -f "$ROOT/$script" ]]; then
        printf 'Bot script not found: %s\n' "$ROOT/$script" >&2
        exit 1
    fi
done

tmux new-session -d -s "$SESSION" -n "Fyers-Nifty" -c "$ROOT"

start_bot() {
    local window="$1"
    local script="$2"
    local command

    tmux set-window-option -t "$SESSION:$window" remain-on-exit on
    printf -v command 'cd %q && exec %q %q' "$ROOT" "$PYTHON" "$ROOT/$script"
    tmux send-keys -t "$SESSION:$window" "$command" C-m
}

start_bot "Fyers-Nifty" "Fyers/BOT_fyers_nifty_g_pool_vE6.py"

tmux new-window -d -t "$SESSION" -n "Fyers-Sensex" -c "$ROOT"
start_bot "Fyers-Sensex" "Fyers/BOT_fyers_sensex_g_pool_v8_9.py"

tmux new-window -d -t "$SESSION" -n "Rmoney-Sensex" -c "$ROOT"
start_bot "Rmoney-Sensex" "Rmoney/BOT_rmoney_sensex_g_pool_v8_9.py"

tmux new-window -d -t "$SESSION" -n "Rmoney-Nifty" -c "$ROOT"
start_bot "Rmoney-Nifty" "Rmoney/BOT_rmoney_nifty_g_pool_vE6.py"

printf 'Started four bot windows in detached tmux session "%s".\n' "$SESSION"
printf 'Attach with: tmux attach -t %s\n' "$SESSION"
