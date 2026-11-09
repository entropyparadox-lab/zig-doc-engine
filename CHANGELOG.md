# Changelog

## 1.5.1 — 2026-11-09

- Pin the stable CI compiler to Zig 0.17.1 (released 2026-11-02), rather than 0.17.0. Keep the package minimum at 0.17.0: this patch adds no newer language or standard-library API requirement.
- Make the CLI `--help` smoke check fail CI on a nonzero exit; remove `|| true`.
- Report the package version, not a hard-coded compiler version, in CLI help.
- Correct English/Korean build prerequisites and distinguish historical Zig 0.16.0 benchmarks from the current compiler. Preserve all versioned 0.16 documentation and benchmark data.
- Update the contributor stable-compiler policy. SQLite3 and libc remain build/link dependencies; no new dependencies are introduced.

### Official sources

- [Zig download index](https://ziglang.org/download/index.json): the `0.17.1` entry gives the release date, platform archives and SHA-256 checksums.
- [Zig 0.17.1 language documentation](https://ziglang.org/documentation/0.17.1/).
- [Zig 0.17.0 release notes](https://ziglang.org/download/0.17.0/release-notes.html): this is the release-notes URL supplied by the official 0.17.1 index entry; do not infer a separate 0.17.1 release-notes page.

### Existing PR #6

Read-only review of [PR #6](https://github.com/entropyparadox-lab/zig-doc-engine/pull/6) found useful but separate Next.js 15 / React 19 / Axum 0.8 documentation work, along with a stale 1.4.1 version bump and historical Zig 0.16 FAQ edits. None is incorporated into this compiler patch: the frontend/Rust additions need their own verification and conflict resolution against 1.5.x. The PR is left open and unchanged; no merge or branch rewrite is performed.
