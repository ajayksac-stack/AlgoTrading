#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"
SCRIPT="$ROOT/dashboard_vDASH9/backend_vDASH8.py"
SESSION="trading-dashboard"

if ! command -v tmux >/dev/null 2>&1; then
    printf 'tmux is not installed. Install it with: sudo apt install tmux\n' >&2
    exit 1
fi

if [[ ! -x "$PYTHON" ]]; then
    printf 'Project Python environment not found or not executable: %s\n' "$PYTHON" >&2
    exit 1
fi

if [[ ! -f "$SCRIPT" ]]; then
    printf 'Dashboard backend not found: %s\n' "$SCRIPT" >&2
    exit 1
fi

if tmux has-session -t "$SESSION" 2>/dev/null; then
    pane_dead="$(tmux display-message -p -t "$SESSION" '#{pane_dead}')"
    pane_command="$(tmux display-message -p -t "$SESSION" '#{pane_current_command}')"
    if [[ "$pane_dead" == "0" ]]; then
        if [[ "$pane_command" == "python" || "$pane_command" == "python3" ]]; then
            printf 'Dashboard is already running in tmux session "%s".\n' "$SESSION"
            printf 'Attach with: tmux attach -t %s\n' "$SESSION"
            exit 0
        fi
        printf 'tmux session "%s" is occupied by "%s"; inspect it before restarting.\n' \
            "$SESSION" "$pane_command" >&2
        exit 1
    fi

    printf -v command 'cd %q && exec %q %q' "$ROOT" "$PYTHON" "$SCRIPT"
    tmux set-window-option -t "$SESSION" remain-on-exit on
    tmux respawn-pane -k -t "$SESSION" "$command"
else
    printf -v command 'cd %q && exec %q %q' "$ROOT" "$PYTHON" "$SCRIPT"
    tmux new-session -d -s "$SESSION" -n "Dashboard" -c "$ROOT" "$command"
    tmux set-window-option -t "$SESSION" remain-on-exit on
fi

printf 'Started dashboard backend in tmux session "%s".\n' "$SESSION"
printf 'Open http://localhost:8000/ for the dashboard.\n'
printf 'Attach with: tmux attach -t %s\n' "$SESSION"
