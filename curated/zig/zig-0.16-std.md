# Zig v0.16.0 Standard Library Reference & Complete Compilable Idioms

## Core v0.16.0+ Breaking Changes
- **`main` Signature**: `pub fn main(init: std.process.Init) !void`
- **CLI Arguments**: `init.minimal.args.iterate()` or `init.arena.allocator()`
- **For Loop Syntax**: Must use `for (items, 0..) |item, idx|` (never `for (items) |item, idx|`).

## 100% Compilable Main Example
```zig
const std = @import("std");

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();

    var args_list: std.ArrayList([]const u8) = .empty;
    defer args_list.deinit(allocator);

    var it = init.minimal.args.iterate();
    while (it.next()) |arg| {
        try args_list.append(allocator, std.mem.sliceTo(arg, 0));
    }
    const args = args_list.items;

    for (args, 0..) |arg, idx| {
        std.debug.print("Arg {d}: {s}\n", .{ idx, arg });
    }
}
```
