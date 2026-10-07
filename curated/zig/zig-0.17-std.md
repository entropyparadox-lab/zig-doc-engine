# Zig v0.17.0 Standard Library Reference & Complete Compilable Idioms

## Core v0.17.0+ Breaking Changes & Invariants
- **`main` Signature**: `pub fn main(init: std.process.Init) !void`
- **CLI Arguments**: `init.minimal.args.iterate()` or `init.arena.allocator()`
- **Allocators**: Use `init.gpa` (process GPA) or `init.arena.allocator()`. `std.heap.smp_allocator` is standard multithreaded allocator; `std.heap.BufferFirstAllocator` replaces `StackFallbackAllocator`.
- **String Formatting**: `try allocator.print("...", .{...})` on `mem.Allocator` (replaces legacy `std.fmt.allocPrint`).
- **Sentinel Slices**: `try allocator.dupeSentinel(u8, slice, 0)` replaces legacy `allocator.dupeZ`.
- **Array Initialization**: Use `@splat(val)` (replaces legacy array multiplication `[1]T{0} ** N`).
- **Enum Int Conversion**: `@backingInt(enum_val)` and `@fromBackingInt(int_val)` replace legacy `@intFromEnum` and `@enumFromInt`.
- **Optimization Mode**: `std.lang.Optimize` (`.debug`, `.safe`, `.fast`, `.small`) replaces legacy `std.builtin.OptimizeMode`.
- **Build System**:
  - `b.createModule` + `.root_module` for all executables and libraries.
  - `run_cmd.addPassthruArgs()` replaces `if (b.args) |args| run_cmd.addArgs(args);`.
  - C headers: Translated via `b.addTranslateC` exposing module `c`.

---

## 100% Compilable Main Example (v0.17.0)

```zig
const std = @import("std");

pub fn main(init: std.process.Init) !void {
    // 1. Allocator setup via std.process.Init
    const allocator = init.arena.allocator();
    const gpa = init.gpa;

    // 2. Parse CLI arguments
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

    // 3. String formatting via mem.Allocator (v0.17.0 idiom)
    const formatted = try allocator.print("CLI parsed {d} arguments successfully", .{args.len});
    defer allocator.free(formatted);

    // 4. Sentinel-terminated string duplication for C-ABI
    const c_str = try allocator.dupeSentinel(u8, formatted, 0);
    defer allocator.free(c_str);

    // 5. Array initialization with @splat
    const buffer: [64]u8 = @splat(0);
    _ = buffer;

    // 6. ArrayList modern navigation
    var numbers: std.ArrayList(u32) = .empty;
    defer numbers.deinit(gpa);
    try numbers.append(gpa, 100);
    try numbers.append(gpa, 200);

    if (numbers.last()) |last_val| {
        std.debug.print("Last number: {d}\n", .{last_val});
    }

    std.debug.print("Zig 0.17.0: {s}\n", .{formatted});
}
```

---

## Modern `build.zig` (v0.17.0)

```zig
const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // 1. Create root module
    const exe_mod = b.createModule(.{
        .root_source_file = b.path("src/main.zig"),
        .target = target,
        .optimize = optimize,
    });

    // 2. Add Executable using root_module
    const exe = b.addExecutable(.{
        .name = "app",
        .root_module = exe_mod,
    });
    b.installArtifact(exe);

    // 3. Run Step with Passthru Args (v0.17.0 idiom)
    const run_cmd = b.addRunArtifact(exe);
    run_cmd.step.dependOn(b.getInstallStep());
    run_cmd.addPassthruArgs();

    const run_step = b.step("run", "Run the application");
    run_step.dependOn(&run_cmd.step);
}
```
