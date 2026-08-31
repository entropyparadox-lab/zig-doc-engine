# zmcp-gateway: High-Performance Native MCP Multiplexer & Tool Hub for Zig 0.16.0+

Package: `https://github.com/entropyparadox-lab/zmcp-gateway`

`zmcp-gateway` consolidates multiple downstream Model Context Protocol (MCP) tool servers into a **single virtual MCP endpoint** with sub-2.2µs routing latency, explicit opt-in caching (`cache_ttl_sec`), and **W3C OpenTelemetry distributed tracing**.

---

## 1. Safety Architecture (Explicit Opt-In Caching Contract)

1. **Default: Pure Pass-Through (`cache_ttl_sec = 0`)**:
   - Polling 도구(`poll_status`), 상태 변이(`company_transfer`), 최신 데이터 조회는 **캐시를 타지 않고 100% 실시간 전달**.
2. **Explicit Opt-In (`cache_ttl_sec > 0`)**:
   - 국가 코드, 정적 스키마 등 작성자가 보증한 불변 메타데이터 도구만 지정된 TTL 동안 인메모리 캐싱 (최대 512 엔트리 LRU 및 만료 시 지연 회수).
3. **Sub-2.2µs Zero-Alloc Routing**:
   - **459,000+ req/sec** 처리량 및 요청별 Arena 메모리 격리로 메모리 누수 0 바이트 보장.
4. **W3C OpenTelemetry Tracing (`zlog`)**:
   - 모든 도구 호출에 `traceparent` (`00-{trace_id}-{span_id}-01`) 자동 주입.

---

## 2. Installation (`build.zig.zon`)

```bash
zig fetch --save https://github.com/entropyparadox-lab/zmcp-gateway/archive/refs/tags/v1.2.0.tar.gz
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
        .version = "1.2.0",
    });
    defer gw.deinit();

    // Register Upstream
    var up = gateway.Upstream.init(allocator, "sys", undefined, myHandler);

    // 1. Dynamic / Polling Tool (Default: cache_ttl_sec = 0 -> 100% Real-time Pass-Through)
    try up.addTool(allocator, .{
        .name = "poll_status",
        .description = "Poll dynamic task status",
        .schema_json = "{}",
        .cache_ttl_sec = 0,
    });

    // 2. Static Metadata Tool (Explicit Opt-In: cache_ttl_sec = 3600 -> Safe Caching)
    try up.addTool(allocator, .{
        .name = "get_country_code",
        .description = "Get static country metadata",
        .schema_json = "{}",
        .cache_ttl_sec = 3600,
    });
    try gw.registerUpstream(up);
}
```
