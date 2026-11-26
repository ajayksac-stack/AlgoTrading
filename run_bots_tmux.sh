#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"
SESSION="trading-bots"
ENV_ENTRIES=()

if [[ -f "$ROOT/.env" ]]; then
    line_number=0
    while IFS= read -r line || [[ -n "$line" ]]; do
        ((line_number += 1))
        if [[ -z "${line//[[:space:]]/}" || "$line" =~ ^[[:space:]]*# ]]; then
            continue
        fi
        if [[ ! "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            printf 'Invalid .env entry at line %d\n' "$line_number" >&2
            exit 1
        fi

        name="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        if [[ "${value:0:1}" == '"' || "${value:0:1}" == "'" ]]; then
            if [[ ${#value} -lt 2 || "${value: -1}" != "${value:0:1}" ]]; then
                printf 'Unclosed quote in .env entry at line %d\n' "$line_number" >&2
                exit 1
            fi
            value="${value:1:${#value}-2}"
        fi
        ENV_ENTRIES+=("$name=$value")
    done < "$ROOT/.env"
fi

if ! command -v tmux >/dev/null 2>&1; then
    printf 'tmux is not installed. Install it with: sudo apt install tmux\n' >&2
    exit 1
fi

if [[ ! -x "$PYTHON" ]]; then
    printf 'Project Python environment not found or not executable: %s\n' "$PYTHON" >&2
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

if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux new-session -d -s "$SESSION" -n "Fyers-Nifty" -c "$ROOT"
fi

for entry in "${ENV_ENTRIES[@]}"; do
    name="${entry%%=*}"
    value="${entry#*=}"
    tmux set-environment -t "$SESSION" "$name" "$value"
done

start_bot() {
    local window="$1"
    local script="$2"
    local command
    local pane_dead
    local pane_command
    local pane_pid
    local pane_args

    printf -v command 'cd %q && exec %q %q' "$ROOT" "$PYTHON" "$ROOT/$script"

    if tmux list-windows -t "$SESSION" -F '#{window_name}' | grep -Fx -- "$window" >/dev/null; then
        pane_dead="$(tmux display-message -p -t "$SESSION:$window" '#{pane_dead}')"
        if [[ "$pane_dead" != "1" ]]; then
            pane_command="$(tmux display-message -p -t "$SESSION:$window" '#{pane_current_command}')"
            pane_pid="$(tmux display-message -p -t "$SESSION:$window" '#{pane_pid}')"
            pane_args="$(ps -p "$pane_pid" -o args=)" || {
                printf 'Unable to inspect process in tmux window "%s"\n' "$window" >&2
                return 1
            }

            if [[ "$pane_args" == "$PYTHON $ROOT/$script" ]]; then
                ((already_running += 1))
                return
            fi
            if [[ "$pane_command" != "bash" && "$pane_command" != "sh" && "$pane_command" != "zsh" ]]; then
                printf 'tmux window "%s" is occupied by "%s"; inspect it before restarting.\n' \
                    "$window" "$pane_command" >&2
                return 1
            fi
        fi

        tmux set-window-option -t "$SESSION:$window" remain-on-exit on
        tmux respawn-pane -k -t "$SESSION:$window" "$command"
        ((started += 1))
        return
    fi

    tmux new-window -d -t "$SESSION" -n "$window" -c "$ROOT"
    tmux set-window-option -t "$SESSION:$window" remain-on-exit on
    tmux send-keys -t "$SESSION:$window" "$command" C-m
    ((started += 1))
}

started=0
already_running=0
start_bot "Fyers-Nifty" "Fyers/BOT_fyers_nifty_g_pool_vE6.py"
start_bot "Fyers-Sensex" "Fyers/BOT_fyers_sensex_g_pool_v8_9.py"
start_bot "Rmoney-Sensex" "Rmoney/BOT_rmoney_sensex_g_pool_v8_9.py"
start_bot "Rmoney-Nifty" "Rmoney/BOT_rmoney_nifty_g_pool_vE6.py"

printf 'Bot startup complete in tmux session "%s": %d started/restarted, %d already running.\n' \
    "$SESSION" "$started" "$already_running"

if [[ -x "$ROOT/run_dashboard_tmux.sh" ]]; then
    if "$ROOT/run_dashboard_tmux.sh"; then
        printf 'Dashboard startup complete: http://localhost:8000/\n'
    else
        printf 'Bots started, but the dashboard could not be started.\n' >&2
        exit 1
    fi
fi

printf 'Attach with: tmux attach -t %s\n' "$SESSION"
