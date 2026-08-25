# Zig v0.16.0 C-ABI Export & Memory Management Idioms

## 1. Allocator Strategies

| Allocator | Use Case | Memory Free Strategy |
| :--- | :--- | :--- |
| `std.heap.ArenaAllocator` | Batch tasks, request handling, CLI parsing | Single `arena.deinit()` frees everything |
| `std.heap.GeneralPurposeAllocator` | Long-lived server objects, leak-tracking | Explicit `deinit()` per allocation with safety checks |
| `std.heap.FixedBufferAllocator` | Embedded, hot paths, stack memory | Zero OS syscalls, fixed max capacity |
| `std.heap.c_allocator` | C-ABI exports, FFI boundary returns | Passed to `free()` or exported deallocator |

### Zero-Leak Arena Pattern
```zig
const std = @import("std");

pub fn processRequest(parent_allocator: std.mem.Allocator, input: []const u8) ![]const u8 {
    var arena = std.heap.ArenaAllocator.init(parent_allocator);
    defer arena.deinit(); // Automatically frees all temporary allocations below
    const allocator = arena.allocator();

    var list: std.ArrayList([]const u8) = .empty;
    var iter = std.mem.splitScalar(u8, input, ',');
    while (iter.next()) |item| {
        try list.append(allocator, try allocator.dupe(u8, item));
    }

    // Only dupe the final result out to the parent allocator
    return try parent_allocator.dupe(u8, list.items[0]);
}
```

## 2. C-ABI FFI Export (`export fn`)

When exporting functions for Python (`ctypes`), Node.js (`ffi-napi`), or C/C++:
1. Use `[*c]const u8` (null-terminated C string) or explicit `ptr + len`.
2. Allocate outgoing memory with `std.heap.c_allocator`.
3. Provide an explicit `free` function so foreign runtimes can safely release memory.

```zig
const std = @import("std");

pub const EngineHandle = ?*anyopaque;

export fn engine_create() EngineHandle {
    const allocator = std.heap.c_allocator;
    const obj = allocator.create(MyEngine) catch return null;
    obj.* = MyEngine.init(allocator);
    return @ptrCast(obj);
}

export fn engine_destroy(handle: EngineHandle) void {
    if (handle) |ptr| {
        const obj: *MyEngine = @ptrCast(@alignCast(ptr));
        obj.deinit();
        std.heap.c_allocator.destroy(obj);
    }
}

export fn engine_execute_json(handle: EngineHandle, query: [*c]const u8) [*c]u8 {
    if (handle == null or query == null) return null;
    const obj: *MyEngine = @ptrCast(@alignCast(handle.?));

    const result_json = obj.process(std.mem.span(query)) catch return null;
    // Returns null-terminated string allocated via c_allocator
    const c_str = std.heap.c_allocator.dupeZ(u8, result_json) catch return null;
    return c_str.ptr;
}

export fn engine_free_string(str: [*c]u8) void {
    if (str != null) {
        std.heap.c_allocator.free(std.mem.span(str));
    }
}
```

## 3. Native Multithreading with `std.Thread`
```zig
const std = @import("std");

fn worker(id: usize, work_items: []const u32) void {
    for (work_items) |item| {
        std.debug.print("Worker {d} processing item {d}\n", .{ id, item });
    }
}

pub fn spawnWorkers(allocator: std.mem.Allocator) !void {
    const thread_count = 4;
    var threads: [thread_count]std.Thread = undefined;

    const data = [_]u32{ 10, 20, 30, 40 };

    for (0..thread_count) |i| {
        threads[i] = try std.Thread.spawn(.{}, worker, .{ i, &data });
    }

    for (threads) |th| {
        th.join();
    }
}
```
