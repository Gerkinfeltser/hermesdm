#!/usr/bin/env bash
# env.sh — Load hermes environment variables before starting HermesDM bot.
# Source this first: source env.sh && python3 -m bot.telegram_handler
#
# Reads MINIMAX_API_KEY from ~/.bashrc (where hermes-agent stores it)
# and from hermes config, then exports them for the Python process.

# Source bashrc for MINIMAX_API_KEY
if [ -f "$HOME/.bashrc" ]; then
    # Disable any interactive prompts in bashrc
    export BASH_ENV="$HOME/.bashrc"
    # Only export lines that set MINIMAX_API_KEY or OPENROUTER
    eval "$(grep -E "^export (MINIMAX_API_KEY|OPENROUTER)" "$HOME/.bashrc" 2>/dev/null)" \
        || true
fi

# Also try to get from hermes config (MCP server env block)
CONFIG="$HOME/.hermes/config.yaml"
if [ -f "$CONFIG" ]; then
    # Extract MINIMAX_API_KEY from the MCP env block in yaml
    MMKEY=$(awk '/^  minimax:/,/^[^ ]/{if(/api_key/)print}' "$CONFIG" 2>/dev/null | grep -o "sk-cp-[^\']*" | head -1)
    if [ -n "$MMKEY" ]; then
        export MINIMAX_API_KEY="$MMKEY"
    fi
fi

# Verify
echo "MINIMAX_API_KEY: ${MINIMAX_API_KEY:0:10}..." 1>&2
