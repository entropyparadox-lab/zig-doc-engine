#!/usr/bin/env python3
"""Run multi-iteration benchmark suite across Rust, Zig, and Go."""

import subprocess
import re
import statistics
import os

BIN_RUST = "/home/cycorld/projects/benchmark-doc-engine/stress-test/rust/target/release/rust-stress-bench"
BIN_ZIG = "/home/cycorld/projects/benchmark-doc-engine/stress-test/zig/zig-out/bin/zig-stress-bench"
BIN_GO = "/home/cycorld/projects/benchmark-doc-engine/stress-test/go/go-stress-bench"

ITERATIONS = 5

def run_test(bin_path: str, lang: str):
    parse_times = []
    index_times = []
    search_qps = []
    
    parse_re = re.compile(r"\[Parse\] \d+ chunks in ([\d\.]+)m?s")
    index_re = re.compile(r"\[Index\] \d+ rows in ([\d\.]+)m?s")
    search_re = re.compile(r"\[Search 8-Threads\] \d+ queries in [\d\.]+m?s \((\d+) QPS\)")

    for i in range(ITERATIONS):
        proc = subprocess.run([bin_path], capture_output=True, text=True)
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        
        # Parse ms
        m_p = parse_re.search(out)
        if m_p:
            parse_times.append(float(m_p.group(1)))
            
        # Index ms
        m_i = index_re.search(out)
        if m_i:
            index_times.append(float(m_i.group(1)))
            
        # Search QPS
        m_s = search_re.search(out)
        if m_s:
            search_qps.append(float(m_s.group(1)))
            
    # Measure memory RSS
    time_proc = subprocess.run(["/usr/bin/time", "-v", bin_path], capture_output=True, text=True)
    rss_re = re.compile(r"Maximum resident set size \(kbytes\): (\d+)")
    m_rss = rss_re.search(time_proc.stderr)
    peak_rss_kb = int(m_rss.group(1)) if m_rss else 0
    
    # Measure binary size (stripped)
    subprocess.run(["strip", bin_path], check=False)
    bin_size_kb = os.path.getsize(bin_path) / 1024.0

    return {
        "lang": lang,
        "parse_ms_mean": statistics.mean(parse_times),
        "parse_ms_stdev": statistics.stdev(parse_times) if len(parse_times) > 1 else 0,
        "index_ms_mean": statistics.mean(index_times),
        "index_ms_stdev": statistics.stdev(index_times) if len(index_times) > 1 else 0,
        "search_qps_mean": statistics.mean(search_qps),
        "search_qps_stdev": statistics.stdev(search_qps) if len(search_qps) > 1 else 0,
        "peak_rss_mb": peak_rss_kb / 1024.0,
        "bin_size_mb": bin_size_kb / 1024.0,
    }

def main():
    print(f"Running {ITERATIONS}-run stress benchmark suite across Rust, Zig, and Go...")
    
    res_zig = run_test(BIN_ZIG, "Zig v0.16.0")
    res_rust = run_test(BIN_RUST, "Rust (AOT)")
    res_go = run_test(BIN_GO, "Go 1.26")
    
    print("\n" + "="*80)
    print(f"{'Metric':<35} | {'Zig v0.16.0':<12} | {'Rust (AOT)':<12} | {'Go 1.26':<12}")
    print("="*80)
    
    print(f"{'1. Markdown Parse (10MB) [ms]':<35} | {res_zig['parse_ms_mean']:>8.2f} ms  | {res_rust['parse_ms_mean']:>8.2f} ms  | {res_go['parse_ms_mean']:>8.2f} ms")
    print(f"{'2. FTS5 Indexing (11k rows) [ms]':<35} | {res_zig['index_ms_mean']:>8.2f} ms  | {res_rust['index_ms_mean']:>8.2f} ms  | {res_go['index_ms_mean']:>8.2f} ms")
    print(f"{'3. 8-Thread Search Throughput [QPS]':<35} | {res_zig['search_qps_mean']:>8.0f} QPS | {res_rust['search_qps_mean']:>8.0f} QPS | {res_go['search_qps_mean']:>8.0f} QPS")
    print(f"{'4. Peak Memory RSS [MB]':<35} | {res_zig['peak_rss_mb']:>8.2f} MB  | {res_rust['peak_rss_mb']:>8.2f} MB  | {res_go['peak_rss_mb']:>8.2f} MB")
    print(f"{'5. Stripped Binary Size [MB]':<35} | {res_zig['bin_size_mb']:>8.2f} MB  | {res_rust['bin_size_mb']:>8.2f} MB  | {res_go['bin_size_mb']:>8.2f} MB")
    print("="*80)

if __name__ == "__main__":
    main()
