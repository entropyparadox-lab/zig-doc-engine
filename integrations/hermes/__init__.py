"""dev-docs plugin entrypoint for Hermes Agent."""
from __future__ import annotations

from typing import Any

from .tools import (
    doc_list,
    doc_read,
    doc_search,
    doc_sync,
    transform_terminal_output,
)

DOC_SEARCH_SCHEMA = {
    "name": "doc_search",
    "description": "Search official documentation and best-practice guides using SQLite FTS5.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Keywords or phrases to search (e.g. 'Router State', 'useActionState', 'argsAlloc')",
            },
            "lib": {
                "type": "string",
                "description": "Optional library/category filter (e.g. 'zig', 'rust', 'axum', 'sqlx', 'react', 'nextjs', 'tailwindcss', 'postgres')",
            },
            "ver": {
                "type": "string",
                "description": "Optional version filter (e.g. '0.16.0', '0.7', '0.8', '18', '19', '3', '4')",
            },
            "limit": {
                "type": "integer",
                "default": 5,
                "description": "Max results to return (default: 5)",
            },
            "tier": {
                "type": "integer",
                "description": "Level of detail: 1 (curated/fast), 2 (specs), 3 (full raw)",
            },
            "auto_detect": {
                "type": "boolean",
                "default": True,
                "description": "When ver is omitted, auto-sniff exact version from Lockfiles/Manifests",
            },
        },
        "required": ["query"],
    },
}

DOC_READ_SCHEMA = {
    "name": "doc_read",
    "description": "Read full documentation content by document ID or relative path (e.g. 'curated:zig-0.16-std', 'curated:axum-0.8').",
    "parameters": {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": "Document ID or path (e.g. 'curated:zig-0.16-std', 'curated:axum-0.8')",
            },
        },
        "required": ["target"],
    },
}

DOC_LIST_SCHEMA = {
    "name": "doc_list",
    "description": "List all indexed libraries, frameworks, categories, and versions in doc-engine.",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

DOC_SYNC_SCHEMA = {
    "name": "doc_sync",
    "description": "Sync documentation from upstream sources and local curated guides.",
    "parameters": {
        "type": "object",
        "properties": {
            "lib": {
                "type": "string",
                "description": "Optional library ID to sync specifically",
            },
        },
    },
}


def _slash_doc(raw_args: str) -> str:
    args = raw_args.strip().split(maxsplit=1)
    if not args:
        return doc_list()
    cmd = args[0].lower()
    sub_arg = args[1] if len(args) > 1 else ""

    if cmd == "list":
        return doc_list()
    if cmd == "get" or cmd == "read":
        return doc_read(sub_arg)
    if cmd == "search":
        return doc_search(sub_arg)

    # Default: search with all args
    return doc_search(raw_args)


def register(ctx: Any) -> None:
    # 1. Register Tools
    ctx.register_tool(
        name="doc_search",
        toolset="doc-engine",
        schema=DOC_SEARCH_SCHEMA,
        handler=lambda params, **kw: doc_search(
            query=params.get("query", ""),
            lib=params.get("lib"),
            ver=params.get("ver"),
            limit=params.get("limit", 5),
            tier=params.get("tier"),
            auto_detect=params.get("auto_detect", True),
            workdir=kw.get("workdir"),
        ),
        emoji="🔍",
    )
    ctx.register_tool(
        name="doc_read",
        toolset="doc-engine",
        schema=DOC_READ_SCHEMA,
        handler=lambda params, **kw: doc_read(target=params.get("target", "")),
        emoji="📖",
    )
    ctx.register_tool(
        name="doc_list",
        toolset="doc-engine",
        schema=DOC_LIST_SCHEMA,
        handler=lambda params, **kw: doc_list(),
        emoji="📚",
    )
    ctx.register_tool(
        name="doc_sync",
        toolset="doc-engine",
        schema=DOC_SYNC_SCHEMA,
        handler=lambda params, **kw: doc_sync(lib=params.get("lib")),
        emoji="🔄",
    )

    # 2. Register Hook (Reactive Compiler Error Remediation)
    ctx.register_hook("transform_terminal_output", transform_terminal_output)

    # 3. Register Slash Command
    ctx.register_command(
        "doc-engine",
        _slash_doc,
        description="Search or read version-accurate developer documentation.",
        args_hint="[search <query> | get <id> | list]",
    )


__all__ = ["doc_search", "doc_read", "doc_list", "doc_sync", "transform_terminal_output", "register"]
