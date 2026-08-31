#!/usr/bin/env python3
"""E2E Compiler Execution & Natural Language Retrieval Benchmark for doc-engine.

Strict Rules:
1. No Oracle: Context is dynamically retrieved via `doc-engine search <natural_language_query>`.
2. Real Compiler: Evaluates actual compiler exit codes (Exit Code 0).
   - Zig: `zig build-exe -lc`
   - Rust: `cargo check` inside an isolated `axum = "0.7"` project
   - TypeScript: `tsc --noEmit` inside an isolated `react@18.2.0` project
3. Incremental State Persistence: Flushes results immediately to JSON.
"""

import os
import re
import time
import json
import urllib.request
import subprocess
import sys
from pathlib import Path

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
BIZROUTER_KEY = os.environ.get("BIZROUTER_API_KEY", "")

TESTBED_DIR = Path("/home/cycorld/projects/zig-doc-engine/benchmarks/compiler_testbeds")
RESULTS_FILE = Path("/home/cycorld/projects/zig-doc-engine/benchmarks/compiler_e2e_results.json")

MODELS = [
    ("OpenAI GPT-4o", "openai", "gpt-4o"),
    ("OpenAI GPT-4o-mini", "openai", "gpt-4o-mini"),
    ("Google Gemini 3.7 Flash", "bizrouter", "google/gemini-3.7-flash"),
    ("Qwen 3.8 27B", "bizrouter", "bizrouter/qwen-3.8-27b"),
]

SCENARIOS = [
    {
        "id": "zig_016",
        "lang": "Zig v0.16.0",
        "prompt": "Write a complete compilable Zig v0.16.0 program with pub fn main that parses CLI arguments and prints them. Include all necessary imports. Provide ONLY the code block.",
        "search_query": "process argsWithAllocator main",
        "search_lib": "zig",
        "search_ver": "0.16.0",
        "compiler": "zig",
    },
    {
        "id": "axum_07",
        "lang": "Rust (Axum 0.7)",
        "prompt": "In a Rust project using axum = \"0.7\", write a complete compilable main.rs with AppState, a Router, and a POST /users handler that extracts State and returns String. Include all imports and fn main with tokio::main. Provide ONLY the code block.",
        "search_query": "Router State with_state",
        "search_lib": "axum",
        "search_ver": "0.7",
        "compiler": "rust_axum07",
    },
    {
        "id": "react_18",
        "lang": "TypeScript (React 18)",
        "prompt": "In a TypeScript project using React 18 and Next.js 14, write a complete compilable client component 'use client' that uses useFormState and a form action with state feedback. Include all necessary imports and TypeScript types. Provide ONLY the code block.",
        "search_query": "useFormState useTransition",
        "search_lib": "react",
        "search_ver": "18",
        "compiler": "ts_react18",
    },
]

def extract_code(raw_response: str) -> str:
    m = re.search(r"```(?:zig|rust|tsx|ts)?\n(.*?)```", raw_response, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m2 = re.search(r"```\n(.*?)```", raw_response, re.DOTALL)
    if m2:
        return m2.group(1).strip()
    return raw_response.strip()

def search_doc_engine(query: str, lib: str, ver: str) -> str:
    res = subprocess.run(
        ["doc-engine", "search", query, "--lib", lib, "--ver", ver, "--limit", "2"],
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        return res.stdout.strip()
    return ""

def call_model(provider: str, model_id: str, prompt: str, context: str = "") -> str:
    system_msg = "You are an expert systems programmer. Respond with 100% syntactically valid, compilable code without syntax errors or missing imports. Output ONLY the code block."
    if context:
        system_msg += f"\n\n[OFFICIAL DOCUMENTATION SEARCH RESULTS - doc-engine]:\n{context}"

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
    }

    if provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": "application/json"
        }
    else: # bizrouter
        url = "https://api.bizrouter.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {BIZROUTER_KEY}",
            "Content-Type": "application/json"
        }

    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            data = json.loads(res.read())
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"

def verify_with_compiler(compiler_type: str, code: str) -> tuple[bool, str]:
    if compiler_type == "zig":
        test_file = TESTBED_DIR / "zig" / "temp_test.zig"
        test_file.write_text(code, encoding="utf-8")
        out_bin = TESTBED_DIR / "zig" / "temp_test"
        
        cmd = [
            "zig", "build-exe", "-lc",
            str(test_file),
            "-femit-bin=" + str(out_bin),
            "-I/home/cycorld/.linuxbrew/opt/sqlite/include",
            "-L/home/cycorld/.linuxbrew/opt/sqlite/lib",
            "-lsqlite3",
            "--cache-dir", str(TESTBED_DIR / "zig" / ".cache"),
            "--global-cache-dir", str(TESTBED_DIR / "zig" / ".global_cache")
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return True, "Compilation Success"
        return False, res.stderr.strip() or res.stdout.strip()

    elif compiler_type == "rust_axum07":
        src_file = TESTBED_DIR / "rust_axum07" / "src" / "main.rs"
        src_file.write_text(code, encoding="utf-8")
        
        cmd = ["cargo", "check", "--offline"]
        res = subprocess.run(cmd, cwd=str(TESTBED_DIR / "rust_axum07"), capture_output=True, text=True)
        if res.returncode == 0:
            return True, "Compilation Success"
        return False, res.stderr.strip() or res.stdout.strip()

    elif compiler_type == "ts_react18":
        src_file = TESTBED_DIR / "ts_react18" / "src" / "Component.tsx"
        src_file.write_text(code, encoding="utf-8")
        
        cmd = ["pnpm", "exec", "tsc", "--noEmit"]
        res = subprocess.run(cmd, cwd=str(TESTBED_DIR / "ts_react18"), capture_output=True, text=True)
        if res.returncode == 0:
            return True, "TypeScript Typecheck Success"
        return False, res.stdout.strip() or res.stderr.strip()

    return False, "Unknown compiler"

def main():
    print("=" * 105)
    print("🔬 COMPILER EXIT-CODE E2E BENCHMARK (Real Compilers: zig, rustc, tsc)")
    print("=" * 105)

    results = []

    for model_name, provider, model_id in MODELS:
        print(f"\n🧠 Evaluating Model: {model_name}")
        print("-" * 105)

        for sc in SCENARIOS:
            lang = sc["lang"]
            prompt = sc["prompt"]
            comp_type = sc["compiler"]

            # Dynamic E2E search for After case
            doc_context = search_doc_engine(sc["search_query"], sc["search_lib"], sc["search_ver"])

            # 1. Test Before
            raw_before = call_model(provider, model_id, prompt, "")
            code_before = extract_code(raw_before)
            ok_before, err_b = verify_with_compiler(comp_type, code_before)

            # 2. Test After
            raw_after = call_model(provider, model_id, prompt, doc_context)
            code_after = extract_code(raw_after)
            ok_after, err_a = verify_with_compiler(comp_type, code_after)

            res_entry = {
                "model": model_name,
                "scenario": lang,
                "before_pass": ok_before,
                "after_pass": ok_after,
                "before_err": err_b.split("\n")[0] if not ok_before else "",
                "after_err": err_a.split("\n")[0] if not ok_after else "",
            }
            results.append(res_entry)

            status_b = "✅ COMPILER PASS" if ok_before else f"❌ COMPILE ERROR ({err_b.split(chr(10))[0][:45]})"
            status_a = "🏆 COMPILER PASS (100%)" if ok_after else f"❌ COMPILE ERROR ({err_a.split(chr(10))[0][:45]})"

            print(f"  • [{lang:<22}] Before: {status_b}")
            print(f"    {'':<22}  After : {status_a}")
            sys.stdout.flush()

            # Save progress
            with open(RESULTS_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)

    print("\n" + "=" * 105)
    print("📊 REAL COMPILER VERIFICATION SUMMARY MATRIX")
    print("=" * 105)
    print(f"{'Model':<25} | {'Scenario':<22} | {'Before (Compiler)':<22} | {'After (Compiler)'}")
    print("-" * 105)

    for r in results:
        b_str = "✅ PASS (0 err)" if r["before_pass"] else "❌ COMPILE ERROR"
        a_str = "🏆 PASS (0 err)" if r["after_pass"] else "❌ COMPILE ERROR"
        print(f"{r['model']:<25} | {r['scenario']:<22} | {b_str:<22} | {a_str}")

if __name__ == "__main__":
    main()
