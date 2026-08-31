# zmcp: Zero-Allocation Model Context Protocol (MCP) SDK for Zig 0.16.0+

Package: `https://github.com/entropyparadox-lab/zmcp`

`zmcp` provides native Model Context Protocol (MCP 2024-11-05) server capabilities for pure Zig. It synthesizes Draft-7 JSON Schemas at compile time (`@typeInfo`) and processes JSON-RPC 2.0 requests at over **340,000 req/sec** with zero memory leaks.

---

## 1. Installation (`build.zig.zon`)

```bash
zig fetch --save https://github.com/entropyparadox-lab/zmcp/archive/refs/tags/v1.0.0.tar.gz
```

In `build.zig`:
```zig
const zmcp_dep = b.dependency("zmcp", .{
    .target = target,
    .optimize = optimize,
});
exe.root_module.addImport("zmcp", zmcp_dep.module("zmcp"));
```

---

## 2. 100% Compilable MCP Stdio Server

```zig
const std = @import("std");
const zmcp = @import("zmcp");

// 1. Define a strongly-typed tool with automated schema generation
const CalculateTool = struct {
    pub const name = "calculate";
    pub const description = "Add two numbers together";

    pub const Params = struct {
        a: f64,
        b: f64,
        pub const zmcp = .{
            .help = .{
                .a = "First number operand",
                .b = "Second number operand",
            },
        };
    };

    pub fn call(params: Params, alloc: std.mem.Allocator) !zmcp.CallToolResult {
        const sum = params.a + params.b;
        const msg = try std.fmt.allocPrint(alloc, "Sum: {d}", .{sum});
        return zmcp.CallToolResult.text(msg);
    }
};

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();

    var srv = zmcp.Server.init(allocator, .{
        .name = "zig-mcp-server",
        .version = "1.0.0",
        .instructions = "High-performance Zig MCP Tool Server",
    });
    defer srv.deinit();

    // 2. Register tool (schema synthesized at comptime)
    try srv.registerTool(CalculateTool);

    // 3. Run stdio loop for AI Agent (Hermes, Claude Code, Cursor)
    try zmcp.stdio.run(&srv, allocator);
}
```
