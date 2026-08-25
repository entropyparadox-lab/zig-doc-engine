#!/usr/bin/env python3
"""Generate a synthetic 10MB markdown documentation dataset for stress benchmarking."""

import os
import random
from pathlib import Path

DATA_DIR = Path("/home/cycorld/projects/benchmark-doc-engine/stress-test/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

WORDS = [
    "router", "state", "extractor", "middleware", "async", "tokio", "handler",
    "compiler", "optimization", "allocator", "memory", "struct", "generic", "trait",
    "unmanaged", "slice", "pointer", "concurrent", "mutex", "channel", "buffer",
    "endpoint", "websocket", "protocol", "serialization", "deserialization", "schema",
    "transaction", "rollback", "commit", "indexing", "vector", "embedding", "retrieval",
    "pipeline", "stream", "filter", "transform", "aggregate", "response", "request"
]

def generate_doc(doc_id: int) -> str:
    lines = []
    lines.append(f"# Documentation Module {doc_id:04d}: Core Architecture")
    lines.append(f"This module describes the internal mechanics and high-performance patterns of system component {doc_id}.\n")
    
    for sec in range(1, 6):
        lines.append(f"## Section {sec}: Advanced {random.choice(WORDS).capitalize()} Implementation")
        lines.append(f"In this section, we analyze the behavior of `{random.choice(WORDS)}` under high throughput.\n")
        
        for p in range(3):
            sentence = " ".join(random.choices(WORDS, k=25)) + "."
            lines.append(f"{sentence.capitalize()} Ensure proper {random.choice(WORDS)} handling to avoid bottlenecks.")
            
        lines.append("\n```rust")
        lines.append(f"pub fn process_event_{doc_id}_{sec}(state: &AppState) -> Result<(), EngineError> {{")
        lines.append(f"    let ctx = state.{random.choice(WORDS)}();")
        lines.append(f"    ctx.execute_{random.choice(WORDS)}()?;")
        lines.append("    Ok(())")
        lines.append("}")
        lines.append("```\n")
        
    return "\n".join(lines)

def main():
    target_bytes = 10 * 1024 * 1024 # 10 MB
    total_bytes = 0
    doc_id = 0
    
    out_file = DATA_DIR / "corpus_10mb.md"
    print(f"Generating ~10MB markdown corpus at {out_file}...")
    
    with open(out_file, "w", encoding="utf-8") as f:
        while total_bytes < target_bytes:
            doc_id += 1
            content = generate_doc(doc_id) + "\n\n---\n\n"
            f.write(content)
            total_bytes += len(content.encode("utf-8"))
            
    print(f"Generated {doc_id} documents, total size: {total_bytes / (1024*1024):.2f} MB")

if __name__ == "__main__":
    main()
