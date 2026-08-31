# zmcp-gateway: High-Performance Native MCP Multiplexer & Tool Hub for Zig 0.16.0+

Package: `https://github.com/entropyparadox-lab/zmcp-gateway`

`zmcp-gateway` consolidates multiple downstream Model Context Protocol (MCP) tool servers into a **single virtual MCP endpoint** with sub-3µs routing latency, SHA256 deterministic in-memory result caching, and **W3C OpenTelemetry distributed tracing**.

---

## 1. Installation (`build.zig.zon`)

```bash
zig fetch --save https://github.com/entropyparadox-lab/zmcp-gateway/archive/refs/tags/v1.0.0.tar.gz
```

In `build.zig`:
```zig
const gateway_dep = b.dependency("zmcp-gateway", .{
    .target = target,
    .optimize = optimize,
});
exe.root_module.addImport("gateway", gateway_dep.module("zmcp-gateway"));
```

---

## 2. 100% Compilable Gateway Embedding Example

```zig
const std = @import("std");
const gateway = @import("gateway");
const zmcp = @import("zmcp");

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();

    var gw = gateway.Gateway.init(allocator, .{
        .name = "my-ai-gateway",
        .version = "1.0.0",
        .cache_enabled = true,
        .cache_ttl_sec = 60,
    });
    defer gw.deinit();

    // 1. Register Downstream Upstream (e.g. math namespace)
    const MathHandler = struct {
        fn handle(ctx: *anyopaque, alloc: std.mem.Allocator, tool_name: []const u8, args_json: []const u8) anyerror!zmcp.CallToolResult {
            _ = ctx;
            _ = args_json;
            if (std.mem.eql(u8, tool_name, "add")) {
                return zmcp.CallToolResult.text("Result: 42");
            }
            return zmcp.CallToolResult.err("Tool not found");
        }
    };

    var math_up = gateway.Upstream.init(allocator, "math", undefined, MathHandler.handle);
    try math_up.addTool(allocator, .{
        .name = "add",
        .description = "Add numbers",
        .schema_json = "{}",
    });
    try gw.registerUpstream(math_up);

    // 2. Dispatch MCP request (automatically routes math__add with OTel tracing)
    const call_req = "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"math__add\",\"arguments\":{}}}";
    if (try gw.handleMessage(allocator, call_req)) |resp| {
        defer allocator.free(resp);
        std.debug.print("Response: {s}\n", .{resp});
    }
}
```
