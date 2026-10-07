const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // Translate C imports for sqlite3 and libc headers
    const translate_c = b.addTranslateC(.{
        .root_source_file = b.path("src/c_imports.h"),
        .target = target,
        .optimize = optimize,
    });
    translate_c.linkSystemLibrary("sqlite3", .{});
    const c_mod = translate_c.createModule();

    // 1. CLI Executable Module
    const cli_mod = b.createModule(.{
        .root_source_file = b.path("src/main.zig"),
        .target = target,
        .optimize = optimize,
    });
    cli_mod.addImport("c", c_mod);
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
    lib_mod.addImport("c", c_mod);
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

    // Unit Tests
    const cli_tests = b.addTest(.{
        .root_module = cli_mod,
    });
    const c_api_tests = b.addTest(.{
        .root_module = lib_mod,
    });
    const run_cli_tests = b.addRunArtifact(cli_tests);
    const run_c_api_tests = b.addRunArtifact(c_api_tests);

    const test_step = b.step("test", "Run unit tests");
    test_step.dependOn(&run_cli_tests.step);
    test_step.dependOn(&run_c_api_tests.step);
}
