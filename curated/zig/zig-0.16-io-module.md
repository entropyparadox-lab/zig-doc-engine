# Zig v0.16.0 `std.Io` Architecture Module Specification

## Tier 2: Complete I/O Reader, Writer & File Interfaces

### 1. `std.Io.Dir` and File Operations
In v0.16.0, filesystem and stream I/O operate via explicit allocator and `init.io` context.

```zig
const std = @import("std");

pub fn readEntireFile(allocator: std.mem.Allocator, file_path: []const u8) ![]u8 {
    const file = try std.fs.cwd().openFile(file_path, .{ .mode = .read_only });
    defer file.close();

    const max_bytes: usize = 16 * 1024 * 1024; // 16MB
    return try file.readToEndAlloc(allocator, max_bytes);
}

pub fn writeAtomicFile(file_path: []const u8, content: []const u8) !void {
    const file = try std.fs.cwd().createFile(file_path, .{ .truncate = true });
    defer file.close();

    try file.writeAll(content);
}
```

### 2. Streaming Line-by-Line Reader
```zig
pub fn processLines(allocator: std.mem.Allocator, file_path: []const u8) !void {
    const file = try std.fs.cwd().openFile(file_path, .{});
    defer file.close();

    var buf_reader = std.io.bufferedReader(file.reader());
    var in_stream = buf_reader.reader();

    var buf: [4096]u8 = undefined;
    while (try in_stream.readUntilDelimiterOrEof(&buf, '\n')) |line| {
        std.debug.print("Line: {s}\n", .{line});
    }
}
```

### 3. In-Memory Fixed Buffer Streams
Zero heap allocations for fast string formatting and serialization:

```zig
pub fn formatBuffer() ![]const u8 {
    var buffer: [256]u8 = undefined;
    var fba = std.heap.FixedBufferAllocator.init(&buffer);
    const allocator = fba.allocator();

    const formatted = try std.fmt.allocPrint(allocator, "ID: {d}, Status: {s}", .{ 100, "ACTIVE" });
    return formatted;
}
```
