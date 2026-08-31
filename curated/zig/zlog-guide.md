# zlog: Zero-Allocation Structured Logger & OpenTelemetry Tracing for Zig 0.16.0+

Package: `https://github.com/entropyparadox-lab/zlog`

`zlog` provides high-performance structured logging and distributed tracing with **zero heap allocations** on the logging fast-path, ANSI colored terminal formatting, production NDJSON streaming, and **W3C TraceContext** (`traceparent`) / **OpenTelemetry OTLP** span correlation.

---

## 1. Installation (`build.zig.zon`)

```bash
zig fetch --save https://github.com/entropyparadox-lab/zlog/archive/refs/tags/v1.0.0.tar.gz
```

In `build.zig`:
```zig
const zlog_dep = b.dependency("zlog", .{
    .target = target,
    .optimize = optimize,
});
exe.root_module.addImport("zlog", zlog_dep.module("zlog"));
```

---

## 2. 100% Compilable Logging & OpenTelemetry Example

```zig
const std = @import("std");
const zlog = @import("zlog");

pub fn main(init: std.process.Init) !void {
    _ = init;

    // 1. Configure Global Logger (0-heap allocation)
    zlog.setFormat(.ansi); // or .ndjson for production JSON
    zlog.setMinLevel(.debug);

    // 2. OpenTelemetry W3C Distributed Tracing
    var span = zlog.startSpan("handle_checkout", null);
    defer span.end();

    const traceparent = span.toTraceparent();

    // 3. Structured Logging with W3C Context
    zlog.info("Processing Payment", .{
        .user_id = @as(u64, 49201),
        .amount_usd = 199.50,
        .traceparent = &traceparent,
        .client_ip = "192.168.1.50",
    });
}
```
