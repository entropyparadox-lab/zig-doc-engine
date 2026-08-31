# zcli: Zero-Allocation Comptime Declarative CLI & Flag Parser for Zig 0.16.0+

Package: `https://github.com/entropyparadox-lab/zcli`

`zcli` converts plain Zig structs and tagged unions into high-performance, type-safe CLI parsers with **zero heap allocations**, ANSI help formatting, and Bash/Zsh/Fish shell completions.

---

## 1. Installation (`build.zig.zon`)

```bash
zig fetch --save https://github.com/entropyparadox-lab/zcli/archive/refs/tags/v1.0.0.tar.gz
```

In `build.zig`:
```zig
const zcli_dep = b.dependency("zcli", .{
    .target = target,
    .optimize = optimize,
});
exe.root_module.addImport("zcli", zcli_dep.module("zcli"));
```

---

## 2. 100% Compilable Declarative CLI Example

```zig
const std = @import("std");
const zcli = @import("zcli");

const ServerConfig = struct {
    host: []const u8 = "127.0.0.1",
    port: u16 = 8080,
    verbose: bool = false,
    workers: ?u32 = null,
    log_level: enum { debug, info, warn, err } = .info,

    // Declarative Comptime Metadata
    pub const zcli = .{
        .name = "my-server",
        .version = "1.0.0",
        .description = "High performance HTTP server",
        .short = .{
            .port = 'p',
            .host = 'h',
            .verbose = 'v',
            .workers = 'w',
        },
        .env = .{
            .port = "SERVER_PORT",
            .host = "SERVER_HOST",
        },
        .help = .{
            .host = "Bind interface address",
            .port = "Listening port",
            .verbose = "Enable debug logging",
            .workers = "Worker thread pool size",
            .log_level = "Logging verbosity",
        },
    };
};

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();

    var args_list: std.ArrayList([]const u8) = .empty;
    defer args_list.deinit(allocator);

    var it = init.minimal.args.iterate();
    while (it.next()) |arg| {
        try args_list.append(allocator, std.mem.sliceTo(arg, 0));
    }

    // Zero-allocation parse (borrows slices directly from args)
    const config = try zcli.parse(ServerConfig, args_list.items);

    std.debug.print("Server running on {s}:{d} (Workers: {?d})\n", .{
        config.host,
        config.port,
        config.workers,
    });
}
```

---

## 3. Subcommands via Tagged Unions

```zig
const Command = union(enum) {
    serve: ServerConfig,
    build: BuildConfig,
    version: void,
};
const cmd = try zcli.parse(Command, args_list.items);
switch (cmd) {
    .serve => |cfg| runServer(cfg),
    .build => |cfg| runBuild(cfg),
    .version => std.debug.print("v1.0.0\n", .{}),
}
```
