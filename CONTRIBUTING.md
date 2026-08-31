# Contributing to zig-doc-engine ⚡

Thank you for contributing to `zig-doc-engine`! We welcome contributions to improve the documentation search and symbol inspection engine for Zig developers and AI coding agents.

---

## 1. Compiler Versioning & Branch Strategy

We maintain a strict **Dual-Branch Strategy**:

* **`main` (Protected)**: Targets **Official Stable Zig (`0.16.x`)**. All production releases (`vX.Y.Z`) are cut exclusively from `main`. Direct push to `main` is prohibited.
* **`zig-master`**: Tracks upstream `ziglang/zig` nightly builds to prepare for compiler/AST changes in advance.
* **`feat/<name>` / `fix/<name>`**: Branch off `main` for stable changes, or off `zig-master` for nightly updates.

---

## 2. Strict Quality & Verification Gate

1. **100% Tested & Verified**: Every PR must include reproducible test coverage (`zig build test`). Unverified code submissions or untested AI-generated patches will be rejected.
2. **Deterministic & Lightweight**: The compiled binary must stay under 1MB with zero C-dependencies.
3. **No Regressions**: Search query latency and FTS5 indexing throughput must not degrade.

---

## 3. Fast Local Development & Git Hooks

Install the lightweight local pre-commit and pre-push hooks:
```bash
./scripts/setup-hooks.sh
```

Before opening a PR, run full local verification:
```bash
# 1. Format code
zig fmt src/ build.zig

# 2. Run unit & integration tests
zig build test
```

---

## 4. Immutable Release & SemVer Policy

* **Semantic Versioning (SemVer 2.0.0)**:
  * `PATCH (1.0.X)`: Bug fixes, documentation improvements.
  * `MINOR (1.X.0)`: New search capabilities, CLI integrations, backwards-compatible additions.
  * `MAJOR (X.0.0)`: Breaking API or CLI changes.
* **Tag Immutability Principle**:
  * **Never modify or delete a published Git tag.**
  * Zig package manager relies on strict content multihashes (`.hash`). Any hotfix requires an immediate next patch bump (`v1.0.2`).

---

## 5. Commit Message Format

We strictly enforce **Conventional Commits**:
```
<type>(<scope>): <subject>

Examples:
  feat(search): add fuzzy token matching for std symbols
  fix(cli): resolve relative path search in workspace
  docs: update MCP server integration guide
```
