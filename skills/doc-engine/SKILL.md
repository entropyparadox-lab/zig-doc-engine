---
name: doc-engine
description: Use when looking up verified, version-accurate documentation for Rust, Zig, React 19, Next.js 15, Tailwind v4, Zod, and MCP.
version: 1.0.0
author: EntropyParadox Lab
license: MIT
metadata:
  hermes:
    tags: [docs, rust, zig, react, nextjs, tailwind, search, fts5, documentation]
---

# doc-engine: Ultra-fast Version-Accurate Documentation Search

Use `doc-engine` whenever implementing code or designing architectures in **Rust**, **Zig v0.16.0+**, **React 19 / Next.js 15**, **Tailwind v4**, **Zod**, or **MCP (Model Context Protocol)** to prevent version mismatches, syntax errors, and LLM hallucinations.

---

## 1. Trigger Conditions

Run `doc-engine` before writing or refactoring code when:
* Using **Zig v0.16.0+** (verifying `std.Io`, `std.process.Init`, `std.ArrayListUnmanaged`, `build.zig`).
* Using **Rust Axum / SQLx / Tokio** (verifying Axum 0.7 vs 0.8 `Router`/`State`, SQLx 0.8 `query!`, `JoinSet`, `select!` cancellation safety).
* Using **React 18 vs 19 / Next.js 14 vs 15** (verifying `useActionState`, `useFormStatus`, Server Actions, Turbopack).
* Using **Tailwind CSS v3 vs v4** (verifying `tailwind.config.js` vs CSS `@theme` directive).
* Building or integrating **MCP (Model Context Protocol)** servers (verifying JSON-RPC 2.0 schemas, `tools/call`, `tools/list`).

---

## 2. Core Commands & Workflows

### A. Version-Scoped Search (`--ver`, `--lib`)
Always pass `--ver` if the project uses a specific major/minor version (e.g. from `Cargo.lock` or `package.json`):

```bash
# 1. Rust Axum 0.8 vs 0.7 Routing & State
doc-engine search "Router State" --lib axum --ver 0.8
doc-engine search "Router State" --lib axum --ver 0.7

# 2. React 18 vs 19 Server Actions & Form Hooks
doc-engine search "useActionState" --lib react --ver 19
doc-engine search "useTransition" --lib react --ver 18

# 3. Next.js 14 vs 15 App Router
doc-engine search "useFormState Server Actions" --lib nextjs --ver 14
doc-engine search "useActionState Turbopack" --lib nextjs --ver 15

# 4. Tailwind CSS v3 vs v4
doc-engine search "@theme" --lib tailwindcss --ver 4
doc-engine search "tailwind.config.js" --lib tailwindcss --ver 3

# 5. Zig v0.16.0 Standard Library & C-ABI
doc-engine search "process argsWithAllocator" --lib zig
doc-engine search "export fn c_allocator" --lib zig

# 6. Tokio & Concurrency Safety
doc-engine search "JoinSet cancellation select" --lib rust

# 7. Model Context Protocol (MCP) Standards
doc-engine search "tools/call initialize" --lib protocols
```

### B. Read Complete Curated Guide
When a snippet is not enough and full architecture context is needed:

```bash
# Get full guide by ID
doc-engine get curated:axum-0.8
doc-engine get curated:zig-0.16-std
doc-engine get curated:tokio-concurrency
doc-engine get curated:zod-type-inference
doc-engine get curated:mcp-spec-2025
```

### C. List Indexed Libraries
```bash
doc-engine list
```

---

## 3. Project-Specific Version Grounding Policy

Before generating code for an existing codebase:
1. **Check Lockfiles First (SSOT)**:
   * Inspect `Cargo.lock` for exact `axum`, `sqlx`, `tokio` versions.
   * Inspect `package-lock.json` / `pnpm-lock.yaml` for exact `react`, `next`, `tailwindcss`, `zod` versions.
2. **Execute Scoped Query**:
   * If `react@18.2.0` is detected, NEVER recommend `useActionState` (React 19). Query with `--ver 18`.
   * If `axum@0.7.5` is detected, NEVER use Axum 0.8 `MethodRouter` nesting. Query with `--ver 0.7`.
   * If `tailwindcss@3.4.0` is detected, NEVER use CSS `@theme`. Query with `--ver 3`.

---

## 4. Common Pitfalls & Rules

* ❌ **DO NOT scrape online docs when doc-engine is available**: Web scraping introduces 100k+ tokens of bloated HTML and triggers output length limits.
* ❌ **DO NOT guess Zig standard library APIs**: Zig v0.16.0 broke nearly all 0.11-0.13 APIs. Always query `doc-engine search "<query>" --lib zig`.
* ❌ **DO NOT mix React 18 and 19 idioms**: Always ground on the project's lockfile before choosing hook APIs.
