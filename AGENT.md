# AI Agent Integration Matrix for `doc-engine`

This guide explains how to integrate `doc-engine` across all major AI coding agents, CLIs, and editor extensions.

---

## 🎯 Quick Matrix: Configuration Files per Tool

| AI Tool / CLI | Config / Instruction File | How It Uses `doc-engine` |
| :--- | :--- | :--- |
| **Hermes Agent** | `~/.hermes/skills/productivity/doc-engine/SKILL.md` | Native skill + `doc_search` tool |
| **Claude Code CLI** | `CLAUDE.md` | Terminal Bash execution before code generation |
| **OpenAI Codex / Aider** | `.aider.conf.yml` or `CONVENTIONS.md` | Automated CLI lookups & prompt grounding |
| **Gemini CLI** | `GEMINI.md` or `.geminirules` | Shell tool execution with `--ver` filters |
| **GitHub Copilot** | `.github/copilot-instructions.md` | Context-grounding guidelines for completions & PRs |
| **Cursor / Windsurf** | `.cursorrules` / `.windsurfrules` | Terminal execution rules before edits |
| **Roo Code / Cline** | `.clinerules` / `.roomodes` | Custom terminal tool invocation |
| **Universal (All Tools)**| **MCP Server (`stdio` mode)** | Native tool call (`doc_search`, `doc_read`) |

---

## 1. OpenAI Codex / Aider (`CONVENTIONS.md` or `.aider.conf.yml`)

Add to `CONVENTIONS.md`:

```markdown
# Documentation & Architecture Guidelines
Always verify library API signatures before generating Rust, Zig, React, or Tailwind code:
1. Inspect project lockfiles (`Cargo.lock`, `package-lock.json`, `pnpm-lock.yaml`) for exact dependency versions.
2. Run `doc-engine search "<query>" --lib <lib> --ver <version>` to retrieve verified code patterns.
3. For Zig v0.16.0+, strictly follow `doc-engine search "<query>" --lib zig` to avoid deprecated APIs.
```

---

## 2. Gemini CLI (`GEMINI.md` or `.geminirules`)

Add to `GEMINI.md`:

```markdown
# Gemini System Instructions
- When implementing code with Rust Axum, SQLx, Tokio, Zig, React 19, or Tailwind v4, use the local `doc-engine` tool.
- Run `doc-engine search "<keywords>" --ver <version>` to avoid cross-version syntax mixing.
- Never hallucinate deprecated Zig v0.11-0.13 standard library APIs.
```

---

## 3. GitHub Copilot (`.github/copilot-instructions.md`)

Add to `.github/copilot-instructions.md`:

```markdown
# Repository Instructions for GitHub Copilot
- This repository uses `doc-engine` for version-accurate local documentation.
- When generating code, ensure compatibility with the exact version declared in lockfiles.
- For React, check if React 18 or 19 is used before proposing `useActionState` or Server Actions.
- For Tailwind, check if v3 (`tailwind.config.js`) or v4 (`@theme`) is used.
```

---

## 4. Claude Code CLI (`CLAUDE.md`)

Add to `CLAUDE.md`:

```markdown
## Documentation Lookup
Before writing code in Rust, Zig, React, Next.js, or Tailwind, query the local documentation engine:
- `doc-engine search "<query>" --lib <lib> --ver <version>`
- `doc-engine get curated:<doc_id>`
```

---

## 5. Cursor & Windsurf (`.cursorrules`)

Add to `.cursorrules`:

```markdown
# Documentation Engine Rules
When writing or refactoring code:
1. Always check project lockfiles (`Cargo.lock`, `pnpm-lock.yaml`, `package-lock.json`) for exact dependency versions.
2. Query `doc-engine search "<query>" --ver <version>` in terminal to look up official idioms before generating code.
3. For Zig v0.16.0+, verify standard library APIs using `doc-engine search "<query>" --lib zig`.
```

---

## 6. Universal MCP Server Setup (Stdio Mode)

Any MCP-compatible client can connect to `doc-engine` directly.

Add to your tool's MCP configuration (`mcpServers`):

```json
{
  "mcpServers": {
    "doc-engine": {
      "command": "doc-engine",
      "args": ["search", "$QUERY", "--limit", "5"]
    }
  }
}
```
