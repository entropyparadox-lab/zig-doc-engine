# Zig v0.17.0 LLM Drift FAQ & Compiler Error Troubleshooting Guide

A curated catalog of compiler errors, build failures, and breaking language / standard library shifts introduced in Zig v0.17.0.

---

## 1. `@cImport` Removed: Invalid Builtin Function

### ❌ Error Symptom
```text
error: invalid builtin function: '@cImport'
const c = @cImport({
          ^~~~~~~~
```

### 🔍 Root Cause
`@cImport` was completely removed from the Zig language in v0.17.0. C translation is now handled via the build system (`b.addTranslateC`) or the standalone `translate-c` package.

### ✅ Modern Fix (v0.17.0+)
1. Create a C header file (e.g. `src/c_imports.h`) with the required `#include` directives:
```c
#ifndef C_IMPORTS_H
#define C_IMPORTS_H
#include <sqlite3.h>
#include <stdio.h>
#include <unistd.h>
#endif
```

2. In `build.zig`, translate the header into a module and add it to your root module:
```zig
const translate_c = b.addTranslateC(.{
    .root_source_file = b.path("src/c_imports.h"),
    .target = target,
    .optimize = optimize,
});
translate_c.linkSystemLibrary("sqlite3", .{});
const c_mod = translate_c.createModule();

exe_mod.addImport("c", c_mod);
```

3. In your Zig source code, import the module directly:
```zig
const c = @import("c");
```

---

## 2. `build.zig`: `no field named 'args' in struct 'Build'`

### ❌ Error Symptom
```text
build.zig:33:11: error: no field named 'args' in struct 'Build'
    if (b.args) |args| {
          ^~~~
```

### 🔍 Root Cause
In Zig v0.17.0, the Maker process was separated from the Configurer process. `b.args` is no longer observable during build script evaluation.

### ✅ Modern Fix (v0.17.0+)
Replace conditional argument forwarding with `addPassthruArgs()`:
```zig
// Legacy (v0.16.0)
// if (b.args) |args| {
//     run_cmd.addArgs(args);
// }

// Modern (v0.17.0+)
run_cmd.addPassthruArgs();
```

---

## 3. `mem.Allocator`: Missing `dupeZ` Member

### ❌ Error Symptom
```text
error: no field or member function named 'dupeZ' in 'mem.Allocator'
    const path_z = allocator.dupeZ(u8, path_span) catch return null;
                   ~~~~~~~~~^~~~~~
```

### 🔍 Root Cause
`allocator.dupeZ` has been removed in favor of explicit sentinel duplication via `dupeSentinel`.

### ✅ Modern Fix (v0.17.0+)
```zig
// Modern (v0.17.0+)
const path_z = try allocator.dupeSentinel(u8, path_span, 0);
defer allocator.free(path_z);
```

---

## 4. `std.fmt.allocPrint`: Moved to `mem.Allocator`

### ❌ Error Symptom / Deprecation
Calling `std.fmt.allocPrint(allocator, ...)` is verbose and deprecated in favor of allocator member methods.

### ✅ Modern Fix (v0.17.0+)
```zig
// Modern (v0.17.0+)
const formatted = try allocator.print("Key: {s}, Count: {d}", .{ key, count });
defer allocator.free(formatted);
```

---

## 5. `void{}` Syntax Removed

### ❌ Error Symptom
```text
error: expected type, found 'void'
    return void{};
```

### 🔍 Root Cause
`void{}` is no longer valid Zig syntax. Empty struct syntax `{}` is used instead.

### ✅ Modern Fix (v0.17.0+)
```zig
// Modern (v0.17.0+)
return {};
```

---

## 6. `errdefer |err|` Capture Syntax Removed

### ❌ Error Symptom
```text
error: cannot capture error in 'errdefer'
    errdefer |err| logError(err);
```

### 🔍 Root Cause
Error capture `|err|` in `errdefer` blocks is no longer permitted (#23734).

### ✅ Modern Fix (v0.17.0+)
Split into an inner function or handle via `catch |err|`:
```zig
pub fn doWork() void {
    doWorkInner() catch |err| {
        std.debug.print("Error occurred: {s}\n", .{@errorName(err)});
    };
}

fn doWorkInner() !void {
    // work logic here
}
```

---

## 7. Array Multiplication Syntax `**` Removed

### ❌ Error Symptom
```text
error: expected ';' after statement, found '**'
    var buf = [1]u8{0} ** 64;
```

### 🔍 Root Cause
Array multiplication syntax `a ** b` was removed in favor of `@splat`.

### ✅ Modern Fix (v0.17.0+)
```zig
// Modern (v0.17.0+)
var buf: [64]u8 = @splat(0);
```

---

## 8. Enum Integer Conversion: `@backingInt` and `@fromBackingInt`

### ❌ Error Symptom / Deprecation
`@intFromEnum` and `@enumFromInt` are deprecated in favor of backing integer builtins.

### ✅ Modern Fix (v0.17.0+)
```zig
const Status = enum(u16) { ok = 200, not_found = 404 };

const code: u16 = @backingInt(Status.ok);
const status: Status = @fromBackingInt(code);
```

---

## 9. `@bitCast` Restrictions: `extern struct` / `extern union`

### ❌ Error Symptom
```text
error: cannot @bitCast from 'extern struct'
```

### 🔍 Root Cause
`@bitCast` now operates strictly on logical bit representations and is endian-agnostic. In-memory type punning for `extern struct` must use `@ptrCast`.

### ✅ Modern Fix (v0.17.0+)
```zig
// Modern (v0.17.0+)
const int_ptr: *align(1) const u16 = @ptrCast(&bytes);
const val: u16 = int_ptr.*;
```

---

## 10. `StackFallbackAllocator` Renamed to `BufferFirstAllocator`

### ❌ Error Symptom
```text
error: root source file struct 'heap' has no member named 'StackFallbackAllocator'
```

### ✅ Modern Fix (v0.17.0+)
```zig
var stack_buf: [256]u8 = undefined;
var stack: std.heap.BufferFirstAllocator = .init(@ptrCast(&stack_buf), gpa);
const allocator = stack.allocator();
```

---

## 11. `std.lang.Optimize` (Formerly `OptimizeMode`)

### ❌ Error Symptom
`std.builtin.OptimizeMode` is deprecated. Tag names have changed from `ReleaseSafe`/`ReleaseFast` to `safe`/`fast`.

### ✅ Modern Fix (v0.17.0+)
```zig
const opt: std.lang.Optimize = .fast; // .debug, .safe, .fast, .small
if (opt.runtimeSafety()) {
    // ...
}
```

---

## 12. `std.ArrayList`: `last()`, `lastPtr()`, `last().?`

### ❌ Error Symptom
`getLastOrNull()` and `getLast()` are deprecated.

### ✅ Modern Fix (v0.17.0+)
```zig
// Modern (v0.17.0+)
if (list.last()) |item| {
    // safe read
}
const item = list.last().?; // non-null assertion
if (list.lastPtr()) |item_ptr| {
    // pointer to last element
}
```

---

## 13. `@hasDecl` Returns True Only for Public Declarations

### 🔍 Semantic Shift
Previously `@hasDecl(T, "field")` returned `true` for private declarations within the same file. In v0.17.0, `@hasDecl` returns `true` **only for `pub` declarations**, regardless of callsite location.

---

## 14. `@divCeil` Builtin Added

### ✅ Modern Fix (v0.17.0+)
```zig
// Replaces std.math.divCeil(a, b) catch unreachable
const result = @divCeil(5, 3); // 2
```
