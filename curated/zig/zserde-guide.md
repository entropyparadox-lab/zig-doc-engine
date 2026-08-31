# zserde: 5-in-1 Zero-Allocation Multi-Format Serialization for Zig 0.16.0+

Package: `https://github.com/entropyparadox-lab/zserde`

`zserde` provides **zero-copy deserialization**, **comptime struct reflection**, and **zero-cost schema validation** across **JSON, MessagePack, CBOR, TOML, and YAML** with 100% pure Zig and zero C dependencies.

---

## 1. Installation (`build.zig.zon`)

```bash
zig fetch --save https://github.com/entropyparadox-lab/zserde/archive/refs/tags/v1.0.1.tar.gz
```

In `build.zig`:
```zig
const zserde_dep = b.dependency("zserde", .{
    .target = target,
    .optimize = optimize,
});
exe.root_module.addImport("zserde", zserde_dep.module("zserde"));
```

---

## 2. API Matrix

| Goal | Function Signature | Memory Overhead |
| :--- | :--- | :--- |
| **Zero-Copy Parse** | `zserde.<format>.fromSliceBorrowed(T, bytes)` | **0 bytes** (borrows string slices directly) |
| **Allocating Parse** | `zserde.<format>.fromSlice(T, allocator, bytes)` | Duplicates strings & dynamic arrays |
| **Serialize to Slice**| `zserde.<format>.toSlice(allocator, value)` | Caller owns returned `[]u8` slice |
| **Validate Struct** | `zserde.validate(value)` | **0 bytes** (Comptime-generated assertions) |

*(Replace `<format>` with `json`, `msgpack`, `cbor`, `toml`, or `yaml`)*

---

## 3. 100% Compilable Zero-Copy JSON & YAML Example

```zig
const std = @import("std");
const zserde = @import("zserde");

const DatabaseConfig = struct {
    host: []const u8,
    port: u16 = 5432,
    max_connections: u32 = 20,
    secret_key: []const u8,

    pub const zserde = .{
        .rename_all = .camelCase,              // max_connections -> "maxConnections"
        .skip = .{ .secret_key = true },       // hides from serialization
        .validate = .{
            .port = .{ .min = 1024, .max = 65535 },
            .host = .{ .starts_with = "127." },
        },
    };
};

pub fn main() !void {
    const raw_json = "{\"host\": \"127.0.0.1\", \"port\": 5432, \"maxConnections\": 50, \"secretKey\": \"token\"}";

    // Zero allocations: parses directly from input slice
    const cfg = try zserde.json.fromSliceBorrowed(DatabaseConfig, raw_json);

    // Comptime-synthesized validation
    try zserde.validate(cfg);

    std.debug.print("Valid config: {s}:{d}\n", .{ cfg.host, cfg.port });
}
```
