const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // 1. CLI Executable Module
    const cli_mod = b.createModule(.{
        .root_source_file = b.path("src/main.zig"),
        .target = target,
        .optimize = optimize,
    });

    cli_mod.linkSystemLibrary("sqlite3", .{});
    cli_mod.link_libc = true;

    const exe = b.addExecutable(.{
        .name = "doc-engine",
        .root_module = cli_mod,
    });
    b.installArtifact(exe);

    // 2. Static Library (C-ABI)
    const lib_mod = b.createModule(.{
        .root_source_file = b.path("src/c_api.zig"),
        .target = target,
        .optimize = optimize,
    });
    lib_mod.linkSystemLibrary("sqlite3", .{});
    lib_mod.link_libc = true;

    const lib = b.addLibrary(.{
        .name = "docengine",
        .root_module = lib_mod,
        .linkage = .static,
    });
    b.installArtifact(lib);

    // Install C Header
    b.installFile("include/doc_engine.h", "include/doc_engine.h");
}
