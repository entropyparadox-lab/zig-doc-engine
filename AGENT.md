# AI Agent Integration Guide for `doc-engine`

This guide explains how to configure and use `doc-engine` across major AI coding agents (**Hermes**, **Claude Code**, **Cursor**, **Windsurf**, and **Roo Code**).

---

## 1. Hermes Agent
`doc-engine` is natively supported via the `dev-docs` plugin and the `doc-engine` skill:

```yaml
# ~/.hermes/skills/productivity/doc-engine/SKILL.md
```
The agent will automatically use `doc_search(query, lib, ver)` with Lockfile-First project sniffing.

---

## 2. Claude Code CLI
Add `doc-engine` to your project's `CLAUDE.md`:

```markdown
## Documentation Lookup
Before writing Rust, Zig, React, Next.js, or Tailwind code, query the local documentation engine to verify exact version signatures:
- `doc-engine search "<query>" --lib <lib> --ver <version>`
- `doc-engine get curated:<doc_id>`
```

---

## 3. Cursor / Windsurf (`.cursorrules`)
Place a `.cursorrules` file in your repository root:

```markdown
# Documentation Engine Rules
When writing or refactoring code:
1. Always check project lockfiles (`Cargo.lock`, `pnpm-lock.yaml`, `package-lock.json`) for exact dependency versions.
2. Query `doc-engine search "<query>" --ver <version>` in terminal to look up official idioms before generating code.
3. For Zig v0.16.0+, verify standard library APIs using `doc-engine search "<query>" --lib zig`.
```

---

## 4. Model Context Protocol (MCP) Mode
`zig-doc-engine` can be wrapped in a simple Stdio MCP server to provide tool definitions (`doc_search`, `doc_read`, `doc_list`) to any MCP-compliant client.
