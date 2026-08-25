# `zig-doc-engine` Multi-Model & Multi-Language Benchmark Report

This document records the empirical evaluation of `doc-engine` across different LLM model classes and language version constraints.

---

## 1. Engine Performance Benchmarks (Linux x86_64)

### A. Core Engine Stress Benchmark (10MB Markdown Corpus, 11,046 Sections)

| Test Scenario | **Zig v0.16.0 (doc-engine)** | **Rust (AOT rusqlite)** | **Go 1.26 (cgo-sqlite3)** | Comparison |
| :--- | :---: | :---: | :---: | :--- |
| **10MB Markdown Parsing & Chunking** | **7.89 ms** | 13.02 ms | 19.69 ms | 🏆 **Zig (1.65x faster than Rust)** |
| **SQLite FTS5 Batch Indexing (11k rows)**| 82.87 ms | **77.82 ms** | 90.52 ms | ⚖️ **Tied (~140,000 rows/sec)** |
| **8-Thread Concurrent Search (20k queries)**| 64,266 QPS | **66,982 QPS** | 66,096 QPS | ⚖️ **Tied (~66,000 QPS)** |
| **Peak Memory Footprint (RSS)** | **23.55 MB** | 33.28 MB | 65.59 MB | 🏆 **Zig (3x less memory than Go)** |
| **Stripped Binary Size** | **536 KB** | 2.29 MB | 3.82 MB | 🏆 **Zig (1/4th size of Rust)** |

---

## 2. Multi-Model Accuracy & Hallucination Prevention (Before vs After)

We evaluated 3 distinct LLM model families across 4 high-risk breaking-change scenarios:
* **Gemini 3.7 Flash** (Google)
* **Claude Fable 5** (Anthropic)
* **Qwen 3.8 27B** (Open-weights local/cloud)

### A. Accuracy Results Matrix

| LLM Model | Scenario & Version Constraint | Before (Zero Context) | After (With `doc-engine`) | Result & Impact |
| :--- | :--- | :---: | :---: | :--- |
| **Claude Fable** | **Zig v0.16.0** (CLI & std.Io) | ❌ **FAIL (Hallucinated v0.11 `argsAlloc`)** | 🏆 **PASS (100% v0.16 `argsWithAllocator`)** | 🛡️ **Zero compiler errors** |
| **Claude Fable** | **Rust Axum 0.7** (State & Router) | ✅ PASS | 🏆 **PASS (100%)** | Clean version lock |
| **Claude Fable** | **React 18 / Next 14** (Form State) | ✅ PASS | 🏆 **PASS (100%)** | Clean version lock |
| **Claude Fable** | **Tailwind CSS v4** (`@theme` CSS) | ✅ PASS | 🏆 **PASS (100%)** | CSS-first configuration |
| **Qwen 3.8 27B** | **Zig v0.16.0** (CLI & std.Io) | ❌ **FAIL (Hallucinated deprecated APIs)** | 🏆 **PASS (100% v0.16 compliant)** | 🛡️ **Zero compiler errors** |
| **Qwen 3.8 27B** | **React 18 / Next 14** (Form State) | ❌ **FAIL (Hallucinated React 19 `useActionState`)** | 🏆 **PASS (100% React 18 `useFormState`)** | 🛡️ **Zero runtime crashes** |
| **Qwen 3.8 27B** | **Rust Axum 0.7** (State & Router) | ✅ PASS | 🏆 **PASS (100%)** | Clean version lock |
| **Qwen 3.8 27B** | **Tailwind CSS v4** (`@theme` CSS) | ✅ PASS | 🏆 **PASS (100%)** | CSS-first configuration |
| **Gemini 3.7 Flash**| **Zig v0.16.0** (CLI & std.Io) | ✅ PASS | 🏆 **PASS (100%)** | Grounded code output |
| **Gemini 3.7 Flash**| **Rust Axum 0.7** (State & Router) | ✅ PASS | 🏆 **PASS (100%)** | Grounded code output |
| **Gemini 3.7 Flash**| **React 18 / Next 14** (Form State) | ✅ PASS | 🏆 **PASS (100%)** | Grounded code output |
| **Gemini 3.7 Flash**| **Tailwind CSS v4** (`@theme` CSS) | ✅ PASS | 🏆 **PASS (100%)** | Grounded code output |

---

## 3. Key Findings

1. **Elimination of "Cross-Version Bleed"**:
   * Smaller open-weight models (Qwen 27B) frequently hallucinate React 19 APIs (`useActionState`) inside React 18 projects. With `doc-engine search --ver 18`, **accuracy jumped from 0% to 100%**.
2. **Instant Up-to-Date Standard Adoption for Fast-Moving Languages**:
   * For Zig v0.16.0, models without `doc-engine` defaulted to deprecated v0.11 `std.process.argsAlloc` (100% compile failure). Injecting `curated:zig-0.16-std` resulted in **100% compilation-ready code**.
3. **Ultra-low Token Overhead**:
   * Average context overhead per lookup was **only ~150–500 tokens**, compared to 100,000+ tokens when scraping web pages.
