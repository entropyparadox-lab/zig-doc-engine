#!/usr/bin/env bash
# ==============================================================================
# zig-doc-engine: AI Coding Agent Hook & Integration Setup Wizard
# Sets up reactive error remediation and documentation search across Hermes,
# Claude Code, Cursor, and MCP clients.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

TARGET="${1:---all}"

echo "======================================================================"
echo "⚡ zig-doc-engine: AI Coding Agent Hook Setup"
echo "======================================================================"

# 1. Hermes Agent Plugin Setup
setup_hermes() {
    echo "▶ Setting up Hermes Agent integration..."
    HERMES_PLUGINS_DIR="${HOME}/.hermes/plugins/dev-docs"
    mkdir -p "${HERMES_PLUGINS_DIR}"
    
    cp -r "${REPO_ROOT}/integrations/hermes/"* "${HERMES_PLUGINS_DIR}/"
    echo "  ✓ Copied dev-docs plugin to ${HERMES_PLUGINS_DIR}"

    if command -v hermes >/dev/null 2>&1; then
        hermes plugins enable dev-docs || true
        echo "  ✓ Enabled dev-docs plugin in Hermes"
    else
        echo "  ℹ hermes CLI not in PATH; plugin will load once Hermes is installed."
    fi
}

# 2. Claude Code Setup
setup_claude() {
    echo "▶ Setting up Claude Code hook integration..."
    CLAUDE_HOOKS_DIR="${HOME}/.claude/hooks"
    mkdir -p "${CLAUDE_HOOKS_DIR}"

    cp "${REPO_ROOT}/integrations/claude-code/remediate-error.sh" "${CLAUDE_HOOKS_DIR}/"
    chmod +x "${CLAUDE_HOOKS_DIR}/remediate-error.sh"
    echo "  ✓ Installed error remediation hook: ${CLAUDE_HOOKS_DIR}/remediate-error.sh"
    echo "  ℹ Add the hook configuration from integrations/claude-code/settings-example.json to ~/.claude/settings.json"
}

# 3. Cursor Rules Setup
setup_cursor() {
    echo "▶ Setting up Cursor / Windsurf rules..."
    if [ -f ".cursorrules" ]; then
        if ! grep -q "doc-engine" .cursorrules; then
            cat "${REPO_ROOT}/integrations/cursor/.cursorrules" >> .cursorrules
            echo "  ✓ Appended doc-engine protocol to existing .cursorrules"
        else
            echo "  ℹ .cursorrules already contains doc-engine protocol."
        fi
    else
        cp "${REPO_ROOT}/integrations/cursor/.cursorrules" .cursorrules
        echo "  ✓ Created .cursorrules in current workspace."
    fi
}

case "${TARGET}" in
    --hermes)
        setup_hermes
        ;;
    --claude)
        setup_claude
        ;;
    --cursor)
        setup_cursor
        ;;
    --all)
        setup_hermes
        setup_claude
        setup_cursor
        ;;
    *)
        echo "Usage: $0 [--all | --hermes | --claude | --cursor]"
        exit 1
        ;;
esac

echo ""
echo "======================================================================"
echo "✅ Setup completed successfully!"
echo "======================================================================"
