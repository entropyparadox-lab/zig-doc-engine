"""Python bridge for Rust/Zig AOT doc-engine with Lockfile-First Project Manifest Sniffer & Reactive Diagnostic Hook."""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PLUGIN_DIR = Path(__file__).resolve().parent
BIN_PATH = PLUGIN_DIR / "bin" / "doc-engine"
GLOBAL_BIN = Path.home() / ".local" / "bin" / "doc-engine"


def _ensure_binary() -> Path:
    if GLOBAL_BIN.exists() and os.access(GLOBAL_BIN, os.X_OK):
        return GLOBAL_BIN
    if BIN_PATH.exists() and os.access(BIN_PATH, os.X_OK):
        return BIN_PATH
    raise FileNotFoundError(f"doc-engine not found at {GLOBAL_BIN} or {BIN_PATH}")


def _run_engine(cmd: list[str]) -> str:
    try:
        binary = _ensure_binary()
        full_cmd = [str(binary)] + cmd
        proc = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            return f"Error ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}"
        return proc.stdout.strip()
    except Exception as e:
        return f"Execution error: {e}"


def detect_project_context(cwd_path: Path | str | None = None) -> tuple[str | None, str | None]:
    """Detect primary language/library ecosystem and exact version using Lockfile-First policy (SSOT)."""
    cwd = Path(cwd_path) if cwd_path else Path.cwd()

    # 1. Zig (build.zig, build.zig.zon)
    if (cwd / "build.zig").exists() or (cwd / "build.zig.zon").exists():
        return "zig", "0.16.0"

    # 2. Rust (Cargo.lock -> Cargo.toml)
    cargo_lock = cwd / "Cargo.lock"
    if cargo_lock.exists():
        try:
            content = cargo_lock.read_text(encoding="utf-8", errors="ignore")
            if 'name = "axum"' in content:
                m = re.search(r'name\s*=\s*"axum"\s+version\s*=\s*"([^"]+)"', content)
                ver = m.group(1) if m else "0.8"
                return "axum", "0.7" if ver.startswith("0.7") else "0.8"
            if 'name = "sqlx"' in content:
                m = re.search(r'name\s*=\s*"sqlx"\s+version\s*=\s*"([^"]+)"', content)
                ver = m.group(1) if m else "0.8"
                return "sqlx", "0.7" if ver.startswith("0.7") else "0.8"
            if 'name = "tokio"' in content:
                return "tokio", "latest"
            return "rust", "latest"
        except Exception:
            pass

    if (cwd / "Cargo.toml").exists():
        try:
            content = (cwd / "Cargo.toml").read_text(encoding="utf-8", errors="ignore")
            if "axum" in content:
                ver = "0.7" if '0.7' in content else "0.8"
                return "axum", ver
            if "sqlx" in content:
                return "sqlx", "0.8"
            return "rust", "latest"
        except Exception:
            pass

    # 3. JavaScript / TypeScript / React / Next.js / Tailwind
    pkg_lock = cwd / "package-lock.json"
    pnpm_lock = cwd / "pnpm-lock.yaml"
    pkg_json = cwd / "package.json"

    if pkg_json.exists():
        try:
            content = pkg_json.read_text(encoding="utf-8", errors="ignore")
            data = json.loads(content)
            deps = {}
            deps.update(data.get("dependencies", {}))
            deps.update(data.get("devDependencies", {}))

            if "next" in deps:
                ver = "15" if "15" in str(deps["next"]) else "14"
                return "nextjs", f"{ver}.x"
            if "react" in deps:
                ver = "19" if "19" in str(deps["react"]) else "18"
                return "react", f"{ver}.x"
            if "tailwindcss" in deps:
                ver = "4" if "4" in str(deps["tailwindcss"]) else "3"
                return "tailwindcss", f"{ver}.x"
            if "zod" in deps:
                return "zod", "latest"
            return "frontend", "latest"
        except Exception:
            pass

    # 4. PostgreSQL / SQL
    if any(cwd.glob("*.sql")) or (cwd / "migrations").exists():
        return "postgres", "latest"

    return None, None


ERROR_PATTERNS: dict[str, list[tuple[str, str | None]]] = {
    "zig": [
        (r"no member named '([^']+)'", None),
        (r"struct '[^']+' has no member named '([^']+)'", None),
        (r"error: no field named '([^']+)'", None),
        (r"root\.main has signature", "main"),
        (r"expected \d+ capture, found \d+", "for loop capture"),
        (r"enum '[^']+' has no tag named '([^']+)'", "callconv"),
        (r"namespace 'std\.posix' has no member named 'getenv'", "getenv"),
        (r"struct 'std\.process' has no member named 'getEnvVarOwned'", "environ"),
    ],
    "rust": [
        (r"no method named `([^`]+)` found", None),
        (r"cannot find (?:function|type|value|struct|enum|macro) `([^`]+)` in", None),
        (r"the trait bound `[^`]+` is not satisfied", "Router State"),
        (r"cannot be shared between threads safely", "State"),
    ],
    "frontend": [
        (r"Property '([^']+)' does not exist on type", None),
        (r"Export (\w+) was not found in", None),
        (r"Cannot find name '([^']+)'", None),
        (r"unknown utility class '([^']+)'", None),
        (r"@theme directive", "@theme"),
    ],
    "postgres": [
        (r'relation "([^"]+)" does not exist', None),
        (r"permission denied for table", "Row Level Security"),
        (r"deadlock detected", "SKIP LOCKED"),
    ],
}


def extract_error_symbols(output: str, category: str) -> list[str]:
    """Extract actionable search keywords from compiler/runtime error output."""
    extracted: list[str] = []
    patterns = ERROR_PATTERNS.get(category, [])

    for regex, fallback_query in patterns:
        matches = re.findall(regex, output)
        if matches:
            if fallback_query:
                extracted.append(fallback_query)
            else:
                for m in matches:
                    if isinstance(m, str) and len(m) > 1:
                        extracted.append(m)

    # Deduplicate preserving order
    return list(dict.fromkeys(extracted))


def transform_terminal_output(
    command: str,
    output: str,
    returncode: int,
    task_id: str = "",
    env_type: str = "",
    **kwargs: Any,
) -> str | None:
    """Reactive Hook: Automatically enrich build/compiler errors with doc-engine v0.16.0+/modern specs."""
    if returncode == 0 or not output:
        return None

    cmd_lower = command.lower()
    # Skip commands that are clearly not build/check/test tools
    relevant_tools = ["zig", "cargo", "tsc", "next", "build", "pnpm", "npm", "yarn", "sqlx", "psql", "make"]
    if not any(tool in cmd_lower for tool in relevant_tools):
        return None

    cwd_val = kwargs.get("cwd") or os.getcwd()
    lib_id, ver = detect_project_context(cwd_val)

    # If lib_id is not detected from files, try to infer from command
    if not lib_id:
        if "zig" in cmd_lower:
            lib_id, ver = "zig", "0.16.0"
        elif "cargo" in cmd_lower:
            lib_id, ver = "rust", "latest"
        elif any(k in cmd_lower for k in ["tsc", "next", "npm", "pnpm", "yarn"]):
            lib_id, ver = "frontend", "latest"
        else:
            return None

    # Map lib_id to error pattern category
    if lib_id in ["zig"]:
        category = "zig"
    elif lib_id in ["rust", "axum", "sqlx", "tokio"]:
        category = "rust"
    elif lib_id in ["react", "nextjs", "tailwindcss", "zod", "frontend"]:
        category = "frontend"
    elif lib_id in ["postgres"]:
        category = "postgres"
    else:
        category = "frontend"

    symbols = extract_error_symbols(output, category)
    if not symbols:
        return None

    # Search top 2 symbols with doc-engine (Tier 1 curated snippets)
    hints: list[str] = []
    for sym in symbols[:2]:
        cmd_args = ["search", sym, "--tier", "1", "--limit", "1"]
        if lib_id and lib_id not in ["rust", "frontend"]:
            cmd_args.extend(["--lib", lib_id])
        if ver and ver != "latest":
            cmd_args.extend(["--ver", ver])

        raw_res = _run_engine(cmd_args)
        items = []
        try:
            items = json.loads(raw_res, strict=False)
        except Exception:
            pass

        # Fallback to unrestricted search if lib-specific returned empty
        if not items and "--lib" in cmd_args:
            fallback_args = ["search", sym, "--tier", "1", "--limit", "1"]
            if ver and ver != "latest":
                fallback_args.extend(["--ver", ver])
            raw_fallback = _run_engine(fallback_args)
            try:
                items = json.loads(raw_fallback, strict=False)
            except Exception:
                pass

        if items and isinstance(items, list):
            doc = items[0]
            snippet = doc.get("snippet", "").replace("<b>", "").replace("</b>", "").strip()
            title = doc.get("title", sym)
            doc_id = doc.get("id", "")
            matched_lib = doc.get("lib_id", lib_id)
            if snippet:
                hints.append(f"• **`{sym}`** (lib: `{matched_lib}`, ref: `{doc_id}`):\n  {snippet[:280]}...")

    if hints:
        ver_tag = f" v{ver}" if ver and ver != "latest" else ""
        banner = (
            f"\n\n════════════════════════════════════════════════════════════════════\n"
            f"💡 [doc-engine{ver_tag} Auto-Remediation Hints]\n"
            + "\n\n".join(hints)
            + f"\n\n(Tip: Run `doc-engine get <id>` or `doc-engine search '<term>' --lib {lib_id}` for full templates)"
            f"\n════════════════════════════════════════════════════════════════════"
        )
        return output + banner

    return None


def doc_search(
    query: str,
    lib: str | None = None,
    ver: str | None = None,
    limit: int = 5,
    tier: int | None = None,
    auto_detect: bool = True,
    workdir: str | Path | None = None,
) -> str:
    """Search official documentation and best-practice guides using SQLite FTS5."""
    effective_ver = ver
    sniffed_hint = ""

    if not effective_ver and auto_detect:
        detected_lib, detected_ver = detect_project_context(workdir)
        if lib and detected_lib == lib.lower() and detected_ver:
            effective_ver = detected_ver
            sniffed_hint = f" (exact lockfile detected: {lib}@{effective_ver})"
        elif not lib and detected_lib and detected_ver:
            lib = detected_lib
            effective_ver = detected_ver
            sniffed_hint = f" (exact lockfile detected: {lib}@{effective_ver})"

    args = ["search", query, "--limit", str(limit)]
    if lib:
        args.extend(["--lib", lib])
    if effective_ver:
        args.extend(["--ver", effective_ver])
    if tier:
        args.extend(["--tier", str(tier)])

    raw = _run_engine(args)
    try:
        data = json.loads(raw, strict=False)
        if not data:
            return f"No documentation matches found for {query!r}{sniffed_hint}"
        lines = [f"Found {len(data)} matches for '{query}'{sniffed_hint}:\n"]
        for item in data:
            ver_tag = f" v{item.get('version')}" if item.get("version") else ""
            lines.append(f"• [{item.get('lib_id')}{ver_tag}] **{item.get('title')}** (`{item.get('id')}`)")
            lines.append(f"  Path: {item.get('path')}")
            snippet = item.get("snippet", "").replace("\n", " ")
            lines.append(f"  Excerpt: {snippet}\n")
        return "\n".join(lines)
    except Exception:
        return raw


def doc_read(target: str) -> str:
    """Read full documentation content by document ID or relative path."""
    return _run_engine(["get", target])


def doc_list() -> str:
    """List all indexed libraries, frameworks, categories, and versions."""
    raw = _run_engine(["list"])
    try:
        data = json.loads(raw, strict=False)
        if not data:
            return "No documents indexed yet."
        lines = ["Indexed Documentation Summary:\n"]
        for row in data:
            lines.append(
                f"- **{row.get('lib_id')}** (v{row.get('version')} / {row.get('category')}): "
                f"{row.get('doc_count')} doc(s), {row.get('total_bytes', 0):,} bytes"
            )
        return "\n".join(lines)
    except Exception:
        return raw


def doc_sync(lib: str | None = None) -> str:
    """Sync documentation from upstream sources and local curated guides."""
    args = ["sync"]
    if lib:
        args.extend(["--id", lib])
    return _run_engine(args)
