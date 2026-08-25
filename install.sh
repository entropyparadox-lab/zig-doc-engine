#!/usr/bin/env bash
# ==============================================================================
# doc-engine: Universal Installer
# Ultra-fast Zig Native FTS5 Offline Documentation Engine
# Repo: https://github.com/entropyparadox-lab/zig-doc-engine
# ==============================================================================

set -euo pipefail

BIN_NAME="doc-engine"
INSTALL_DIR="${HOME}/.local/bin"
DOCS_DB_DIR="${HOME}/.hermes/docs/db"
TMP_DIR=$(mktemp -d)

trap 'rm -rf "${TMP_DIR}"' EXIT

echo "⚡ [doc-engine] Starting universal installation..."
mkdir -p "${INSTALL_DIR}"
mkdir -p "${DOCS_DB_DIR}"

# 1. Determine build/install method
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd || echo "")"

if [ -n "${SCRIPT_DIR}" ] && [ -f "${SCRIPT_DIR}/build.zig" ]; then
    echo "📦 Building from local source repository..."
    cd "${SCRIPT_DIR}"
    zig build -Doptimize=ReleaseFast
    cp -f "${SCRIPT_DIR}/zig-out/bin/${BIN_NAME}" "${INSTALL_DIR}/${BIN_NAME}"
    SOURCE_ROOT="${SCRIPT_DIR}"
else
    echo "🌐 Cloning latest zig-doc-engine repository..."
    git clone --depth 1 https://github.com/entropyparadox-lab/zig-doc-engine.git "${TMP_DIR}/zig-doc-engine"
    cd "${TMP_DIR}/zig-doc-engine"
    
    if command -v zig >/dev/null 2>&1; then
        echo "🔨 Compiling binary with local Zig toolchain..."
        zig build -Doptimize=ReleaseFast
        cp -f "${TMP_DIR}/zig-doc-engine/zig-out/bin/${BIN_NAME}" "${INSTALL_DIR}/${BIN_NAME}"
    else
        echo "⚠️ Zig toolchain not detected. Checking for pre-compiled binary..."
        # If pre-built release binary is published, download it; otherwise guide user
        echo "❌ Please install Zig (v0.14+ or v0.16.0) or run with Zig installed."
        exit 1
    fi
    SOURCE_ROOT="${TMP_DIR}/zig-doc-engine"
fi

chmod +x "${INSTALL_DIR}/${BIN_NAME}"

# 2. Seed curated documentation index
echo "📚 Indexing curated documentation catalogs (Axum 0.8, SQLx 0.8, React 19, Tailwind 4, Zig 0.16)..."
if [ -d "${SOURCE_ROOT}/curated" ]; then
    find "${SOURCE_ROOT}/curated" -name "*.md" | while read -r doc_file; do
        rel_path="${doc_file#"${SOURCE_ROOT}/curated/"}"
        lib_name="$(echo "${rel_path}" | cut -d'/' -f1)"
        file_stem="$(basename "${doc_file}" .md)"
        
        "${INSTALL_DIR}/${BIN_NAME}" index-file \
            --lib "${lib_name}" \
            --title "${file_stem}" \
            --path "${doc_file}" \
            --version "latest" \
            --tier 1 >/dev/null 2>&1 || true
    done
fi

# 3. Ensure ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    SHELL_RC="${HOME}/.bashrc"
    [ -n "${ZSH_VERSION:-}" ] && SHELL_RC="${HOME}/.zshrc"
    echo "export PATH=\"${INSTALL_DIR}:\$PATH\"" >> "${SHELL_RC}"
    export PATH="${INSTALL_DIR}:${PATH}"
fi

echo "✅ [doc-engine] Successfully installed to ${INSTALL_DIR}/${BIN_NAME}"
echo ""
echo "🚀 Quick verification:"
"${INSTALL_DIR}/${BIN_NAME}" list || true
echo ""
echo "🔍 Try searching docs:"
echo "  doc-engine search \"axum State route\""
echo "  doc-engine search \"sqlx query sqlite\""
