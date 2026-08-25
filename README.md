# zig-doc-engine

> **Ultra-lightweight (<550KB), blazing-fast documentation indexing and FTS5 search engine written in Zig v0.16.0.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Zig](https://img.shields.io/badge/Zig-0.16.0-orange.svg)](https://ziglang.org/)
[![Language: English](https://img.shields.io/badge/Language-English-green.svg)](#)
[![Language: 한국어](https://img.shields.io/badge/Language-한국어-red.svg)](README.ko.md)

`zig-doc-engine` is an embedded, zero-dependency documentation search engine designed for AI coding agents, developer CLI tools, and edge devices. It combines zero-copy markdown parsing with embedded SQLite FTS5 full-text indexing, delivering sub-millisecond cold starts and throughput over 65,000 queries/second.

---

## ⚡ Performance Highlights (vs Rust & Go)

Benchmarked on Linux x86_64 across a synthetic **10MB documentation corpus (11,046 sections)** and **20,000 multi-threaded queries**:

| Metric | **zig-doc-engine (Zig v0.16.0)** | **Rust (AOT rusqlite)** | **Go 1.26 (cgo-sqlite3)** | Winner / Advantage |
| :--- | :---: | :---: | :---: | :--- |
| **Markdown Chunking (10MB)** | **7.89 ms** | 13.02 ms | 19.69 ms | 🏆 **Zig (1.65x faster than Rust)** |
| **FTS5 Batch Indexing (11k rows)** | 82.87 ms | **77.82 ms** | 90.52 ms | ⚖️ **Tied (~140,000 rows/sec)** |
| **8-Thread Search Throughput** | 64,266 QPS | **66,982 QPS** | 66,096 QPS | ⚖️ **Tied (~66,000 QPS)** |
| **Peak Memory Footprint (RSS)** | **23.55 MB** | 33.28 MB | 65.59 MB | 🏆 **Zig (3x less memory than Go)** |
| **Stripped Binary Size** | **535 KB** | 2.29 MB | 3.82 MB | 🏆 **Zig (1/4th size of Rust)** |

---

## 🚀 Key Features

* **Zero-copy Parsing**: Ingests multi-megabyte markdown files without heap allocation churn using Zig memory slices.
* **Embedded SQLite FTS5**: Leverages battle-tested SQLite FTS5 for ranked BM25 search, snippet generation, and boolean filtering.
* **Sub-millisecond Cold Starts**: Native AOT binary starts in ~1.2ms with zero VM or runtime overhead.
* **Dual Target Output**: Builds both a standalone CLI binary (`doc-engine`) and a static C-ABI library (`libdocengine.a`) with C headers.
* **Pluggable Data Sources**: Indexes `llms.txt`, official markdown specs, and local documentation repositories.
* **Empirical Multi-Model Benchmarks**: Verified accuracy improvements across **Gemini, Claude Fable, and Qwen** (see [BENCHMARK.md](BENCHMARK.md)).
* **AI Agent Ready**: Pre-configured rules and skills for **Hermes, Claude Code, OpenAI Codex, Gemini CLI, GitHub Copilot, Cursor, Windsurf, and Roo Code** (see [AGENT.md](AGENT.md)).

---

## 🛠️ Installation & Quick Start

### 1. Build from Source
Requires [Zig v0.16.0](https://ziglang.org/download/) and `sqlite3`:

```bash
git clone https://github.com/entropyparadox-lab/zig-doc-engine.git
cd zig-doc-engine
zig build -Doptimize=ReleaseFast
```

The compiled artifacts will be in `zig-out/`:
* `zig-out/bin/doc-engine`: Single standalone CLI binary (~535KB stripped)
* `zig-out/lib/libdocengine.a`: C-compatible static library
* `zig-out/include/doc_engine.h`: C header interface

---

## 📖 CLI Usage

### Search Documentation
```bash
# General search
doc-engine search "Router State"

# Filter by library and limit results
doc-engine search "ArrayListUnmanaged" --lib zig --limit 3
```

### View Document Content
```bash
doc-engine get curated:axum-0.8
```

### List Indexed Libraries
```bash
doc-engine list
```

---

## 🔌 C-ABI Embedding (Python, Node.js, C/C++)

`zig-doc-engine` exports a standard C interface defined in `include/doc_engine.h`.

```c
#include "doc_engine.h"
#include <stdio.h>

int main() {
    DocEngineHandle db = doc_engine_open("/path/to/docs.db", true);
    if (!db) return 1;

    char* json_results = doc_engine_search_json(db, "State Router", NULL, 5);
    printf("Results:\n%s\n", json_results);

    doc_engine_free_string(json_results);
    doc_engine_close(db);
    return 0;
}
```

---

## 📂 Project Structure

```
.
├── include/
│   └── doc_engine.h       # C-ABI export header
├── src/
│   ├── main.zig           # Standalone CLI entrypoint
│   ├── engine.zig         # SQLite FTS5 core engine
│   └── c_api.zig          # C-ABI export functions
├── benchmarks/            # Reproducible benchmark suite
├── build.zig              # Zig v0.16.0 build configuration
├── LICENSE                # MIT License
├── README.md              # English documentation
└── README.ko.md           # 한국어 문서
```

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
