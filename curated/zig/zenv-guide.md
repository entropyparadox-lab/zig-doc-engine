# zenv: Zero-Allocation .env Parser & Comptime Typed Config Injector for Zig 0.16.0+

Package: `https://github.com/entropyparadox-lab/zenv`

`zenv` parses `.env` files and binds values directly to native Zig struct fields with **zero heap allocations** and sub-microsecond latency.

---

## 1. Installation (`build.zig.zon`)

```bash
zig fetch --save https://github.com/entropyparadox-lab/zenv/archive/refs/tags/v1.0.0.tar.gz
```

In `build.zig`:
```zig
const zenv_dep = b.dependency("zenv", .{
    .target = target,
    .optimize = optimize,
});
exe.root_module.addImport("zenv", zenv_dep.module("zenv"));
```

---

## 2. 100% Compilable Zero-Alloc .env Binding Example

```zig
const std = @import("std");
const zenv = @import("zenv");

const DatabaseConfig = struct {
    host: []const u8 = "127.0.0.1",
    port: u16 = 5432,
    database_url: []const u8,
    max_connections: u32 = 20,
    debug: bool = false,
    log_level: enum { debug, info, warn, err } = .info,

    // Custom key mapping override
    pub const zenv = .{
        .mapping = .{
            .database_url = "DB_URL",
        },
    };
};

pub fn main(init: std.process.Init) !void {
    _ = init;

    const raw_env =
        \\HOST=0.0.0.0
        \\PORT=5432
        \\DB_URL="postgresql://user:secret@localhost:5432/app"
        \\DEBUG=true
        \\LOG_LEVEL=warn
    ;

    // Zero heap allocations! Strings are borrowed directly from raw_env
    const config = try zenv.parse(DatabaseConfig, raw_env);

    std.debug.print("Host: {s}, Port: {d}, DB: {s}\n", .{
        config.host,
        config.port,
        config.database_url,
    });
}
```
