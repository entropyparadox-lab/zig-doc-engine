# Zig v0.16.0 Standard Library Reference & Idioms

## Core Changes in Zig v0.16.0+
- **`std.Io` Architecture**: Modern I/O interfaces replacing legacy streams.
- **Process Initialization**: `std.process.Init` and explicit argument parsing with allocators.
- **Unmanaged Data Structures**: `std.ArrayListUnmanaged`, `std.StringHashMapUnmanaged` preferred for tight memory control.
- **Root build.zig Module API**: `b.createModule`, `exe.root_module.addImport`.

## CLI Arguments & Process Idioms
```zig
const std = @import("std");

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    var args = try std.process.argsWithAllocator(allocator);
    defer args.deinit();

    // Skip binary name
    _ = args.skip();

    while (args.next()) |arg| {
        std.debug.print("Arg: {s}\n", .{arg});
    }
}
```

## Fast File Reading & Memory Management
```zig
const std = @import("std");

pub fn readFileContent(allocator: std.mem.Allocator, file_path: []const u8) ![]u8 {
    const file = try std.fs.cwd().openFile(file_path, .{});
    defer file.close();

    const max_bytes: usize = 10 * 1024 * 1024; // 10MB limit
    return try file.readToEndAlloc(allocator, max_bytes);
}
```

## Unmanaged ArrayList Pattern
```zig
const std = @import("std");

pub fn collectItems(allocator: std.mem.Allocator) !void {
    var list = std.ArrayListUnmanaged(u32){};
    defer list.deinit(allocator);

    try list.append(allocator, 10);
    try list.append(allocator, 20);
    try list.append(allocator, 30);

    for (list.items) |item| {
        std.debug.print("Item: {d}\n", .{item});
    }
}
```

## build.zig in v0.16.0
```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const exe = b.addExecutable(.{
        .name = "my-tool",
        .root_source_file = b.path("src/main.zig"),
        .target = target,
        .optimize = optimize,
    });

    b.installArtifact(exe);

    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());

    const run_step = b.step("run", "Run the app");
    run_step.dependOn(&run_cmd.step);
}
```
