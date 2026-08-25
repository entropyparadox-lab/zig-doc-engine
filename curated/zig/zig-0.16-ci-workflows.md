# Zig v0.16.0 CI/CD & GitHub Actions Automation Guide

## 1. Release Artifact Naming Scheme & Target Triples
Since Zig 0.14.1 / 0.15.0-dev.631+, the official release tarball naming convention changed from `zig-{os}-{arch}-{version}` to target-triple aligned `zig-{arch}-{os}-{version}`:
- **Modern (v0.14.1+)**: `zig-x86_64-linux-0.16.0.tar.xz`, `zig-aarch64-macos-0.16.0.tar.xz`, `zig-x86_64-windows-0.16.0.zip`
- **Legacy (<v0.14.1)**: `zig-linux-x86_64-0.14.0.tar.xz`

Official download base URLs:
- **Tagged Releases**: `https://ziglang.org/download/{version}/`
- **Nightly/Dev Builds**: `https://ziglang.org/builds/`

## 2. GitHub Actions Setup (`mlugg/setup-zig@v2`)
Always use **`mlugg/setup-zig@v2`** (or later) for Zig v0.14.1 ~ v0.16.0+.
`mlugg/setup-zig@v1` is deprecated and fails with HTTP 404 because it attempts to download with the legacy `zig-{os}-{arch}` filename from `ziglang.org/builds`.

### Canonical Multi-Platform CI Workflow (`.github/workflows/ci.yml`)
```yaml
name: CI

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  build-and-test:
    name: Build & Test (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Zig v0.16.0
        uses: mlugg/setup-zig@v2
        with:
          version: 0.16.0
          use-cache: true

      - name: Install SQLite3 (Ubuntu)
        if: runner.os == 'Linux'
        run: sudo apt-get update && sudo apt-get install -y libsqlite3-dev

      - name: Build ReleaseFast
        run: zig build -Doptimize=ReleaseFast

      - name: Verify CLI Binary
        run: |
          ./zig-out/bin/doc-engine --help || true
          ls -lh ./zig-out/bin/doc-engine
          ls -lh ./zig-out/lib/libdocengine.a
```

## 3. Dynamic Version Resolution via `build.zig.zon`
With `mlugg/setup-zig@v2`, omitting the `version` field allows the action to automatically detect `minimum_zig_version` from `build.zig.zon`:

```zig
// build.zig.zon
.{
    .name = .my_project,
    .version = "0.1.0",
    .minimum_zig_version = "0.16.0",
    .dependencies = .{},
    .paths = .{""},
}
```

```yaml
      - name: Setup Zig from build.zig.zon
        uses: mlugg/setup-zig@v2
        # Automatically detects minimum_zig_version: 0.16.0
```

## 4. Cache Best Practices
- `use-cache: true` caches the global Zig compilation cache (`.zig-cache`).
- In self-hosted or matrix runners, specify `cache-key: ${{ matrix.os }}` to prevent cache collisions across different architectures.
