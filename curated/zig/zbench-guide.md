# zbench: Criterion.rs-Grade Statistical Microbenchmarking for Zig 0.16.0+

Package: `https://github.com/entropyparadox-lab/zbench`

`zbench` provides statistical microbenchmarking, compiler-elision-proof `blackBox` fences, Tukey's outlier filtering, sub-nanosecond monotonic timing, and terminal ANSI sparkline reporting in pure Zig.

---

## 1. Installation (`build.zig.zon`)

```bash
zig fetch --save https://github.com/entropyparadox-lab/zbench/archive/refs/tags/v1.0.0.tar.gz
```

In `build.zig`:
```zig
const zbench_dep = b.dependency("zbench", .{
    .target = target,
    .optimize = .ReleaseFast,
});
exe.root_module.addImport("zbench", zbench_dep.module("zbench"));
```

---

## 2. 100% Compilable Microbenchmark Example

```zig
const std = @import("std");
const zbench = @import("zbench");

fn benchSha256() void {
    var data: [1024]u8 = undefined;
    @memset(&data, 0x5a);
    var hash: [32]u8 = undefined;
    std.crypto.hash.sha2.Sha256.hash(&data, &hash, .{});
    _ = zbench.blackBox(hash);
}

fn benchSorting() void {
    var array: [256]u32 = undefined;
    for (&array, 0..) |*item, idx| {
        item.* = @as(u32, @intCast(256 - idx));
    }
    std.mem.sort(u32, &array, {}, comptime std.sort.asc(u32));
    _ = zbench.blackBox(array);
}

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();

    var suite = zbench.BenchmarkSuite.init(allocator);
    defer suite.deinit();

    try suite.add("SHA256 (1KB Buffer)", benchSha256, .{
        .warmup_ms = 100,
        .sample_count = 50,
        .bytes_per_op = 1024,
    });

    try suite.add("QuickSort (256 integers)", benchSorting, .{
        .warmup_ms = 100,
        .sample_count = 50,
    });

    try suite.run();
}
```
