# zfetch: Ergonomic, Type-Safe HTTP Client & REST Wrapper for Zig 0.16.0+

Package: `https://github.com/entropyparadox-lab/zfetch`

`zfetch` encapsulates Zig 0.16.0 `std.http.Client` boilerplate into concise, 1-line requests with automatic TLS CA bundle scanning, streaming response buffer management, Bearer token authorization, and typed JSON response deserialization.

---

## 1. Installation (`build.zig.zon`)

```bash
zig fetch --save https://github.com/entropyparadox-lab/zfetch/archive/refs/tags/v1.0.0.tar.gz
```

In `build.zig`:
```zig
const zfetch_dep = b.dependency("zfetch", .{
    .target = target,
    .optimize = optimize,
});
exe.root_module.addImport("zfetch", zfetch_dep.module("zfetch"));
```

---

## 2. 100% Compilable HTTP GET & Typed JSON Example

```zig
const std = @import("std");
const zfetch = @import("zfetch");

const UserProfile = struct {
    id: u64,
    name: []const u8,
    email: []const u8,
    is_active: bool = true,
};

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();
    const io = init.io;

    var client = zfetch.Client.init(allocator, io);
    defer client.deinit();

    // 1-line typed JSON GET request
    var user_resp = try client.getJson(UserProfile, "https://api.example.com/v1/me", .{
        .bearer_token = "ey...",
    });
    defer user_resp.deinit();

    const user = user_resp.value;
    std.debug.print("User: {s} <{s}>\n", .{ user.name, user.email });
}
```
