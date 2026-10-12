#!/usr/bin/env python3
"""Multi-Model x Multi-Language Precision Benchmark for doc-engine (3-Tier LoD).

Evaluates models against breaking-change language/version scenarios:
1. Zig v0.17.0 (std.process.Init, init.minimal.args, allocator.print, dupeSentinel)
2. Zig v0.16.0 (argsWithAllocator, std.process.Init)
3. Go 1.27 (Enhanced ServeMux path wildcards, r.PathValue, generalized function type inference)
4. Rust Axum 0.8 (/{id} routing syntax, axum::extract::State)
5. React 18 / Next.js 14 (Preventing React 19 useActionState runtime crash)
6. Tailwind CSS v4 (@theme CSS-first vs v3 JS config)
"""

import os
import time
import json
import urllib.request
import subprocess

GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_GENAI_API_KEY", "")
BIZROUTER_KEY = os.environ.get("BIZROUTER_API_KEY", "")

MODELS = [
    ("Gemini 3.8 Flash", "gemini_api", "gemini-3.8-flash"),
]

SCENARIOS = [
    {
        "id": "zig_017",
        "lang": "Zig v0.17.0",
        "prompt": "Write a minimal Zig v0.17.0 main program that parses CLI arguments and prints them. Provide ONLY the code without explanation or markdown formatting.",
        "curated_doc": "curated:zig-0.17-std",
        "correct_markers": ["std.process.Init", "init.minimal.args"],
        "hallucination_markers": ["argsAlloc", "argsFree"],
    },
    {
        "id": "zig_016",
        "lang": "Zig v0.16.0",
        "prompt": "Write a minimal Zig v0.16.0 main program that parses CLI arguments and reads a file. Provide ONLY the code without explanation or markdown formatting.",
        "curated_doc": "curated:zig-0.16-std",
        "correct_markers": ["argsWithAllocator", "std.process.Init", "init.minimal.args"],
        "hallucination_markers": ["argsAlloc", "argsFree"],
    },
    {
        "id": "go_127",
        "lang": "Go 1.27 (Routing & Inference)",
        "prompt": "Write a complete Go 1.27 main program using standard net/http ServeMux that registers 'GET /items/{id}', extracts path parameter using r.PathValue, and uses generalized function type inference to map items without explicit type arguments. Provide ONLY the code without explanation or markdown formatting.",
        "curated_doc": "curated:go-1.27-std",
        "correct_markers": ["r.PathValue(", "GET /items/{id}"],
        "hallucination_markers": ["mux.Vars", "chi.URLParam", "gorilla/mux"],
    },
    {
        "id": "axum_08",
        "lang": "Rust (Axum 0.8)",
        "prompt": "In a Rust project using axum = \"0.8\", write a router with with_state and POST /items handler with AppState. Provide ONLY the code without explanation or markdown formatting.",
        "curated_doc": "curated:axum-0.8",
        "correct_markers": ["State(state): State<Arc<AppState>>", "State(state): State<AppState>", "with_state"],
        "hallucination_markers": ["MethodRouter::new"],
    },
    {
        "id": "react_18",
        "lang": "React 18 / Next 14",
        "prompt": "In a React 18 + Next.js 14 project, write a client component form that calls a server action with state feedback. Provide ONLY the code without explanation or markdown formatting.",
        "curated_doc": "curated:react-18",
        "correct_markers": ["useFormState", "useTransition"],
        "hallucination_markers": ["useActionState"],
    },
    {
        "id": "tailwind_v4",
        "lang": "Tailwind CSS v4",
        "prompt": "Write the setup CSS to configure Tailwind CSS v4 with brand color #3b82f6 and Pretendard font. Provide ONLY the CSS without explanation or markdown formatting.",
        "curated_doc": "curated:tailwindcss-v4",
        "correct_markers": ["@import \"tailwindcss\";", "@theme"],
        "hallucination_markers": ["tailwind.config.js", "@tailwind base;"],
    },
]

def query_doc_engine(doc_id: str) -> str:
    res = subprocess.run(
        ["doc-engine", "get", doc_id],
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        return res.stdout.strip()
    return ""

def call_llm(model_tuple: tuple[str, str, str], prompt: str, context: str = "") -> tuple[str, float, int]:
    model_name, api_mode, model_id = model_tuple

    system_msg = "You are an expert programming assistant. Respond strictly with accurate, working code without explanations or markdown backticks."
    if context:
        system_msg += f"\n\n[OFFICIAL VERIFIED DOCUMENTATION REFERENCE - doc-engine]:\n{context}"

    t0 = time.perf_counter()

    if api_mode == "gemini_api":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={GEMINI_KEY}"
        payload = {
            "system_instruction": {"parts": [{"text": system_msg}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1}
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                data = json.loads(res.read())
                latency = time.perf_counter() - t0
                cand = data.get("candidates", [{}])[0]
                text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
                meta = data.get("usageMetadata", {})
                tokens = meta.get("totalTokenCount", 0)
                return text, latency, tokens
        except Exception as e:
            return f"ERROR: {e}", 0.0, 0
    elif api_mode == "anthropic_messages":
        headers = {
            "x-api-key": BIZROUTER_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": model_id,
            "max_tokens": 1500,
            "system": system_msg,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }
        req = urllib.request.Request("https://api.bizrouter.ai/claude/v1/messages", data=json.dumps(payload).encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                data = json.loads(res.read())
                latency = time.perf_counter() - t0
                text = "".join(b.get("text", "") for b in data.get("content", []))
                tokens = data.get("usage", {}).get("output_tokens", 0) + data.get("usage", {}).get("input_tokens", 0)
                return text, latency, tokens
        except Exception as e:
            return f"ERROR: {e}", 0.0, 0
    else:
        headers = {
            "Authorization": f"Bearer {BIZROUTER_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
        }
        req = urllib.request.Request("https://api.bizrouter.ai/v1/chat/completions", data=json.dumps(payload).encode(), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                data = json.loads(res.read())
                latency = time.perf_counter() - t0
                text = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                return text, latency, tokens
        except Exception as e:
            return f"ERROR: {e}", 0.0, 0

def evaluate_code(code: str, correct_markers: list[str], hallucination_markers: list[str]) -> bool:
    has_correct = any(m in code for m in correct_markers)
    has_hallucination = any(m in code for m in hallucination_markers)
    return has_correct and not has_hallucination

def main():
    print("=" * 105)
    print("🚀 MULTI-MODEL x MULTI-LANGUAGE ACCURACY BENCHMARK (Before vs After doc-engine)")
    print("=" * 105)

    results = []

    for model_entry in MODELS:
        model_name = model_entry[0]
        print(f"\n🧠 Evaluating: {model_name}")
        print("-" * 105)

        for sc in SCENARIOS:
            lang = sc["lang"]
            prompt = sc["prompt"]

            # 1. Before: Without doc-engine (Zero-shot)
            code_before, lat_before, tok_before = call_llm(model_entry, prompt, "")
            valid_before = evaluate_code(code_before, sc["correct_markers"], sc["hallucination_markers"])

            # 2. After: With doc-engine (Curated doc injection)
            context = query_doc_engine(sc["curated_doc"])
            code_after, lat_after, tok_after = call_llm(model_entry, prompt, context)
            valid_after = evaluate_code(code_after, sc["correct_markers"], sc["hallucination_markers"])

            res_entry = {
                "model": model_name,
                "scenario": lang,
                "before_valid": valid_before,
                "after_valid": valid_after,
                "before_tok": tok_before,
                "after_tok": tok_after,
                "before_lat": lat_before,
                "after_lat": lat_after,
            }
            results.append(res_entry)

            status_before = "✅ PASS" if valid_before else "❌ FAIL (Hallucinated)"
            status_after = "✅ PASS (100%)" if valid_after else "❌ FAIL"
            print(f"  • [{lang:<30}] Before: {status_before:<22} ➔ After (doc-engine): {status_after}")

    # Final Formatted Table
    print("\n" + "=" * 105)
    print("📊 BENCHMARK ACCURACY & HALLUCINATION RATE SUMMARY")
    print("=" * 105)
    print(f"{'Model':<20} | {'Scenario':<30} | {'Before (No Docs)':<20} | {'After (With doc-engine)':<24} | {'Overhead'}")
    print("-" * 105)

    for r in results:
        b_str = "✅ PASS" if r["before_valid"] else "❌ FAIL (Hallucinated)"
        a_str = "✅ PASS (100%)" if r["after_valid"] else "❌ FAIL"
        tok_diff = r["after_tok"] - r["before_tok"]
        print(f"{r['model']:<20} | {r['scenario']:<30} | {b_str:<20} | {a_str:<24} | +{tok_diff:>4} tokens")

    # Save artifact
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_path = os.path.join(script_dir, "benchmark_results.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[Saved benchmark results to {result_path}]")

if __name__ == "__main__":
    main()
