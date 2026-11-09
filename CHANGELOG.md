# Changelog

## 1.5.1 — 2026-11-09

- Pin the stable CI compiler to Zig 0.17.1 (released 2026-11-02), rather than 0.17.0. Keep the package minimum at 0.17.0: this patch adds no newer language or standard-library API requirement.
- Make the CLI `--help` smoke check fail CI on a nonzero exit; remove `|| true`.
- Report the package version, not a hard-coded compiler version, in CLI help.
- Correct English/Korean build prerequisites and distinguish historical Zig 0.16.0 benchmarks from the current compiler. Preserve all versioned 0.16 documentation and benchmark data.
- Update the contributor stable-compiler policy. SQLite3 and libc remain build/link dependencies; no new dependencies are introduced.
- Serialize CLI search/list and C-ABI search responses with the standard JSON encoder, escaping multiline snippets, quotes, backslashes, and control characters. Add strict JSON round-trip regression coverage against an isolated database.
- Correct library `total_bytes` to count UTF-8 bytes rather than Unicode characters, exposed by the round-trip fixture.

### Official sources

- [Zig download index](https://ziglang.org/download/index.json): the `0.17.1` entry gives the release date, platform archives and SHA-256 checksums.
- [Zig 0.17.1 language documentation](https://ziglang.org/documentation/0.17.1/).
- [Zig 0.17.0 release notes](https://ziglang.org/download/0.17.0/release-notes.html): this is the release-notes URL supplied by the official 0.17.1 index entry; do not infer a separate 0.17.1 release-notes page.

### Existing PR #6

Selectively incorporate four verified documentation files from [PR #6](https://github.com/entropyparadox-lab/zig-doc-engine/pull/6): Next.js 15, React 19, Axum 0.8, and the Axum extractor module. Correct the examples and preserve the current 1.5.1 package version rather than adopting the stale 1.4.1 bump. Enterprise React, SolidJS, Svelte, and historical Zig 0.16 FAQ changes remain unadopted. PR #6 stays open: it is not fully superseded. No merge or branch rewrite is performed.
