# zmcp-gateway: High-Performance Native MCP Multiplexer & Tool Hub for Zig 0.16.0+

Package: `https://github.com/entropyparadox-lab/zmcp-gateway`

`zmcp-gateway` consolidates multiple downstream Model Context Protocol (MCP) tool servers into a **single virtual MCP endpoint** with sub-3µs routing latency, SHA256 deterministic in-memory result caching, and **W3C OpenTelemetry distributed tracing**.

---

## 1. Safety Architecture (Adversarial Hardening)

1. **Read-Only Cache Isolation**:
   - Only idempotent read queries (`get`, `list`, `search`, `query`, `read`, `describe`, `fetch`, `view`, `check`, `status`, `ping`) are cached.
   - Any state-mutation tool (`create`, `update`, `delete`, `transfer`, `approve`, `submit`, `repay`, etc.) **strictly bypasses cache**.
2. **Mutation Cache Invalidation**:
   - When a mutation tool succeeds, all cached queries for that namespace are automatically invalidated to prevent stale reads.
3. **Transparent Tool Naming Resolution**:
   - Supports exact tool names (`mcp__earnlearning__wallet_get`), namespace delimiter (`earnlearning__wallet_get`), and dot format (`earnlearning.wallet_get`).

---

## 2. Installation (`build.zig.zon`)

```bash
zig fetch --save https://github.com/entropyparadox-lab/zmcp-gateway/archive/refs/tags/v1.0.1.tar.gz
```

---

## 3. Embedding Example

```zig
const std = @import("std");
const gateway = @import("gateway");
const zmcp = @import("zmcp");

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();

    var gw = gateway.Gateway.init(allocator, .{
        .name = "my-ai-gateway",
        .version = "1.0.1",
        .cache_enabled = true,
        .cache_ttl_sec = 60,
    });
    defer gw.deinit();

    // Register Upstream
    const ELHandler = struct {
        fn handle(ctx: *anyopaque, alloc: std.mem.Allocator, tool_name: []const u8, args_json: []const u8) anyerror!zmcp.CallToolResult {
            _ = ctx;
            _ = args_json;
            if (std.mem.eql(u8, tool_name, "wallet_get")) {
                return zmcp.CallToolResult.text("{\"balance\": 1000}");
            }
            return zmcp.CallToolResult.err("Tool not found");
        }
    };

    var el_up = gateway.Upstream.init(allocator, "earnlearning", undefined, ELHandler.handle);
    try el_up.addTool(allocator, .{
        .name = "wallet_get",
        .description = "Get current wallet balance",
        .schema_json = "{}",
    });
    try gw.registerUpstream(el_up);

    // Call tool (routes mcp__earnlearning__wallet_get with OTel trace & caching)
    const call_req = "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"mcp__earnlearning__wallet_get\",\"arguments\":{}}}";
    if (try gw.handleMessage(allocator, call_req)) |resp| {
        defer allocator.free(resp);
        std.debug.print("Response: {s}\n", .{resp});
    }
}
```
