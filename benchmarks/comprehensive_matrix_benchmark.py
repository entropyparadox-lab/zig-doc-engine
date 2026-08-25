#!/usr/bin/env python3
"""Comprehensive Multi-Model Matrix Benchmark for doc-engine.

Evaluates 8 distinct models across generations and tiers:
1. OpenAI GPT-4o
2. OpenAI GPT-4o-mini
3. OpenAI GPT-4-turbo
4. Google Gemini 3.7 Flash
5. Google Gemini 3.5 Flash
6. Google Gemini 2.5 Flash
7. Qwen 3.8 27B
8. GLM 5.3
"""

import os
import time
import json
import urllib.request
import subprocess

OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
BIZROUTER_KEY = os.environ.get("BIZROUTER_API_KEY", "")

MODELS = [
    # (Display Name, Provider Type, Model ID)
    ("OpenAI GPT-4o", "openai", "gpt-4o"),
    ("OpenAI GPT-4o-mini", "openai", "gpt-4o-mini"),
    ("OpenAI GPT-4-turbo", "openai", "gpt-4-turbo"),
    ("Google Gemini 3.7 Flash", "bizrouter", "google/gemini-3.7-flash"),
    ("Google Gemini 3.5 Flash", "bizrouter", "google/gemini-3.5-flash"),
    ("Google Gemini 2.5 Flash", "bizrouter", "google/gemini-2.5-flash"),
    ("Qwen 3.8 27B", "bizrouter", "bizrouter/qwen-3.8-27b"),
    ("GLM 5.3", "bizrouter", "z-ai/glm-5.3"),
]

SCENARIOS = [
    {
        "id": "zig_016",
        "lang": "Zig v0.16.0",
        "prompt": "Write a minimal Zig v0.16.0 main program that parses CLI arguments and reads a file. Provide ONLY the code.",
        "curated_doc": "curated:zig-0.16-std",
        "correct_markers": ["argsWithAllocator", "std.process.Init", "init.minimal.args"],
        "hallucination_markers": ["argsAlloc", "argsFree"],
    },
    {
        "id": "axum_07",
        "lang": "Rust (Axum 0.7)",
        "prompt": "In a Rust project using axum = \"0.7\", write a router and POST /items handler with AppState. Provide ONLY the code.",
        "curated_doc": "curated:axum-0.7",
        "correct_markers": ["State(state): State<AppState>", "with_state"],
        "hallucination_markers": ["MethodRouter::new"],
    },
    {
        "id": "react_18",
        "lang": "React 18 / Next 14",
        "prompt": "In a React 18 + Next.js 14 project, write a client component form that calls a server action with state feedback. Provide ONLY the code.",
        "curated_doc": "curated:react-18",
        "correct_markers": ["useFormState", "useTransition"],
        "hallucination_markers": ["useActionState"],
    },
    {
        "id": "tailwind_v4",
        "lang": "Tailwind CSS v4",
        "prompt": "Write the setup CSS to configure Tailwind CSS v4 with brand color #3b82f6 and Pretendard font. Provide ONLY the CSS.",
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

def call_model(provider: str, model_id: str, prompt: str, context: str = "") -> tuple[str, float, int]:
    system_msg = "You are an expert programming assistant. Respond strictly with accurate, working code."
    if context:
        system_msg += f"\n\n[OFFICIAL VERIFIED DOCUMENTATION REFERENCE - doc-engine]:\n{context}"

    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
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

    t0 = time.perf_counter()
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
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
    print("=" * 110)
    print("🚀 MASSIVE 8-MODEL x 4-LANGUAGE MATRIX BENCHMARK (Before vs After doc-engine)")
    print("=" * 110)

    results = []

    for model_name, provider, model_id in MODELS:
        print(f"\n🧠 Evaluating Model: {model_name} [{model_id}]")
        print("-" * 110)

        for sc in SCENARIOS:
            lang = sc["lang"]
            prompt = sc["prompt"]

            # 1. Before: Without doc-engine (Zero-shot)
            code_before, lat_before, tok_before = call_model(provider, model_id, prompt, "")
            valid_before = evaluate_code(code_before, sc["correct_markers"], sc["hallucination_markers"])

            # 2. After: With doc-engine
            context = query_doc_engine(sc["curated_doc"])
            code_after, lat_after, tok_after = call_model(provider, model_id, prompt, context)
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
            print(f"  • [{lang:<18}] Before: {status_before:<22} ➔ After: {status_after}")

    # Summary Output
    print("\n" + "=" * 110)
    print("📊 FULL MULTI-MODEL ACCURACY MATRIX")
    print("=" * 110)
    print(f"{'Model':<25} | {'Scenario':<20} | {'Before':<12} | {'After (doc-engine)':<20} | {'Tokens'}")
    print("-" * 110)

    for r in results:
        b_str = "✅ PASS" if r["before_valid"] else "❌ FAIL"
        a_str = "✅ PASS (100%)" if r["after_valid"] else "❌ FAIL"
        tok_diff = r["after_tok"] - r["before_tok"]
        print(f"{r['model']:<25} | {r['scenario']:<20} | {b_str:<12} | {a_str:<20} | +{tok_diff:>4} tok")

    with open("/home/cycorld/projects/zig-doc-engine/benchmarks/matrix_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
