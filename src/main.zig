const std = @import("std");
const engine = @import("engine.zig");

const c = @cImport({
    @cInclude("stdio.h");
    @cInclude("unistd.h");
    @cInclude("sys/wait.h");
});

fn writeFd(bytes: []const u8) void {
    _ = c.write(1, bytes.ptr, bytes.len);
}

fn readFileContent(allocator: std.mem.Allocator, file_path: []const u8) ![]u8 {
    const path_z = try allocator.dupeZ(u8, file_path);
    defer allocator.free(path_z);

    const f = c.fopen(path_z.ptr, "rb") orelse return error.FileNotFound;
    defer _ = c.fclose(f);

    _ = c.fseek(f, 0, 2); // SEEK_END
    const size: usize = @intCast(c.ftell(f));
    _ = c.fseek(f, 0, 0); // SEEK_SET

    const buf = try allocator.alloc(u8, size);
    const read_bytes = c.fread(buf.ptr, 1, size, f);
    return buf[0..read_bytes];
}

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();

    var args_list: std.ArrayList([]const u8) = .empty;
    defer args_list.deinit(allocator);

    var it = init.minimal.args.iterate();
    while (it.next()) |arg| {
        try args_list.append(allocator, std.mem.sliceTo(arg, 0));
    }
    const args = args_list.items;

    if (args.len < 2 or std.mem.eql(u8, args[1], "--help") or std.mem.eql(u8, args[1], "-h") or std.mem.eql(u8, args[1], "help")) {
        std.debug.print(
            \\doc-engine (Zig Edition v0.16.0) - High-performance Documentation FTS5 Engine
            \\
            \\Usage:
            \\  doc-engine search <query> [--lib <lib>] [--ver <version>] [--tier <1|2|3>] [--limit <n>]
            \\  doc-engine get <id | path | lib>
            \\  doc-engine list
            \\  doc-engine index-file --lib <lib> --title <title> --path <path> [--version <ver>] [--tier <1|2|3>]
            \\  doc-engine sync [--only <libs>] [--category <cat>] [--id <source_id>]
            \\
        , .{});
        if (args.len < 2) {
            std.process.exit(1);
        } else {
            return;
        }
    }

    const cmd = args[1];

    const home = init.minimal.environ.getAlloc(allocator, "HOME") catch ".";
    const db_path = try std.fs.path.join(allocator, &[_][]const u8{ home, ".hermes", "docs", "db", "docs.db" });
    const db_path_c = try allocator.dupeZ(u8, db_path);

    if (std.mem.eql(u8, cmd, "search")) {
        var query_opt: ?[]const u8 = null;
        var lib_opt: ?[]const u8 = null;
        var ver_opt: ?[]const u8 = null;
        var tier_opt: ?usize = null;
        var limit: usize = 5;

        var i: usize = 2;
        while (i < args.len) : (i += 1) {
            const arg = args[i];
            if (std.mem.eql(u8, arg, "--lib") and i + 1 < args.len) {
                i += 1;
                lib_opt = args[i];
            } else if ((std.mem.eql(u8, arg, "--ver") or std.mem.eql(u8, arg, "--version")) and i + 1 < args.len) {
                i += 1;
                ver_opt = args[i];
            } else if (std.mem.eql(u8, arg, "--tier") and i + 1 < args.len) {
                i += 1;
                tier_opt = std.fmt.parseInt(usize, args[i], 10) catch null;
            } else if (std.mem.eql(u8, arg, "--limit") and i + 1 < args.len) {
                i += 1;
                limit = std.fmt.parseInt(usize, args[i], 10) catch 5;
            } else if (query_opt == null and !std.mem.startsWith(u8, arg, "--")) {
                query_opt = arg;
            }
        }

        const query = query_opt orelse {
            std.debug.print("Error: search query required\n", .{});
            std.process.exit(1);
        };

        var eng = engine.Engine.open(allocator, db_path_c, true) catch |err| {
            std.debug.print("Failed to open DB: {}\n", .{err});
            std.process.exit(1);
        };
        defer eng.close();

        // Sanitize query
        var sanitized: std.ArrayList(u8) = .empty;
        defer sanitized.deinit(allocator);

        var token_iter = std.mem.tokenizeSequence(u8, query, " ");
        var first = true;
        while (token_iter.next()) |word| {
            if (!first) try sanitized.append(allocator, ' ');
            try sanitized.append(allocator, '"');
            for (word) |ch| {
                if (ch != '"') try sanitized.append(allocator, ch);
            }
            try sanitized.append(allocator, '"');
            first = false;
        }

        const results = try eng.search(sanitized.items, lib_opt, ver_opt, tier_opt, limit);

        writeFd("[\n");
        for (results, 0..) |r, idx| {
            if (idx > 0) writeFd(",\n");
            const row_json = try std.fmt.allocPrint(allocator,
                \\  {{
                \\    "id": "{s}",
                \\    "lib_id": "{s}",
                \\    "title": "{s}",
                \\    "category": "{s}",
                \\    "version": "{s}",
                \\    "tier": {d},
                \\    "path": "{s}",
                \\    "snippet": "{s}"
                \\  }}
            , .{ r.id, r.lib_id, r.title, r.category, r.version, r.tier, r.path, r.snippet });
            defer allocator.free(row_json);
            writeFd(row_json);
        }
        writeFd("\n]\n");
    } else if (std.mem.eql(u8, cmd, "get")) {
        if (args.len < 3) {
            std.debug.print("Error: target id/path required\n", .{});
            std.process.exit(1);
        }
        const target = args[2];

        var eng = engine.Engine.open(allocator, db_path_c, true) catch |err| {
            std.debug.print("Failed to open DB: {}\n", .{err});
            std.process.exit(1);
        };
        defer eng.close();

        if (try eng.getDocContent(target)) |content| {
            writeFd(content);
            if (!std.mem.endsWith(u8, content, "\n")) writeFd("\n");
        } else {
            std.debug.print("Document not found: {s}\n", .{target});
            std.process.exit(1);
        }
    } else if (std.mem.eql(u8, cmd, "list")) {
        var eng = engine.Engine.open(allocator, db_path_c, true) catch |err| {
            std.debug.print("Failed to open DB: {}\n", .{err});
            std.process.exit(1);
        };
        defer eng.close();

        const list = try eng.listLibraries();

        writeFd("[\n");
        for (list, 0..) |item, idx| {
            if (idx > 0) writeFd(",\n");
            const item_json = try std.fmt.allocPrint(allocator,
                \\  {{
                \\    "lib_id": "{s}",
                \\    "category": "{s}",
                \\    "version": "{s}",
                \\    "tier": {d},
                \\    "doc_count": {d},
                \\    "total_bytes": {d}
                \\  }}
            , .{ item.lib_id, item.category, item.version, item.tier, item.doc_count, item.total_bytes });
            defer allocator.free(item_json);
            writeFd(item_json);
        }
        writeFd("\n]\n");
    } else if (std.mem.eql(u8, cmd, "index-file")) {
        var lib_opt: ?[]const u8 = null;
        var title_opt: ?[]const u8 = null;
        var path_opt: ?[]const u8 = null;
        var ver_opt: []const u8 = "latest";
        var cat_opt: []const u8 = "curated";
        var tier_opt: usize = 1;

        var i: usize = 2;
        while (i < args.len) : (i += 1) {
            const arg = args[i];
            if (std.mem.eql(u8, arg, "--lib") and i + 1 < args.len) {
                i += 1;
                lib_opt = args[i];
            } else if (std.mem.eql(u8, arg, "--title") and i + 1 < args.len) {
                i += 1;
                title_opt = args[i];
            } else if (std.mem.eql(u8, arg, "--path") and i + 1 < args.len) {
                i += 1;
                path_opt = args[i];
            } else if ((std.mem.eql(u8, arg, "--ver") or std.mem.eql(u8, arg, "--version")) and i + 1 < args.len) {
                i += 1;
                ver_opt = args[i];
            } else if (std.mem.eql(u8, arg, "--category") and i + 1 < args.len) {
                i += 1;
                cat_opt = args[i];
            } else if (std.mem.eql(u8, arg, "--tier") and i + 1 < args.len) {
                i += 1;
                tier_opt = std.fmt.parseInt(usize, args[i], 10) catch 1;
            }
        }

        if (lib_opt == null or path_opt == null) {
            std.debug.print("Error: --lib and --path are required for index-file\n", .{});
            std.process.exit(1);
        }

        const file_path = path_opt.?;
        const title = title_opt orelse "untitled";

        const content = readFileContent(allocator, file_path) catch |err| {
            std.debug.print("Failed to read file {s}: {}\n", .{ file_path, err });
            std.process.exit(1);
        };
        defer allocator.free(content);

        var eng = engine.Engine.open(allocator, db_path_c, false) catch |err| {
            std.debug.print("Failed to open DB: {}\n", .{err});
            std.process.exit(1);
        };
        defer eng.close();

        const doc_id = try std.fmt.allocPrint(allocator, "{s}:{s}", .{ lib_opt.?, title });
        defer allocator.free(doc_id);

        try eng.indexDocument(doc_id, lib_opt.?, title, cat_opt, ver_opt, tier_opt, file_path, content);
        std.debug.print("Indexed document: {s}\n", .{doc_id});
    } else if (std.mem.eql(u8, cmd, "sync")) {
        const sync_runner = try std.fs.path.join(allocator, &[_][]const u8{ home, ".hermes", "plugins", "dev-docs", "target", "release", "doc-engine" });
        const sync_runner_c = try allocator.dupeZ(u8, sync_runner);

        var child_args = try std.ArrayList(?[*c]const u8).initCapacity(allocator, args.len + 2);
        try child_args.append(allocator, sync_runner_c.ptr);
        try child_args.append(allocator, "sync");

        var i: usize = 2;
        while (i < args.len) : (i += 1) {
            const arg_c = try allocator.dupeZ(u8, args[i]);
            try child_args.append(allocator, arg_c.ptr);
        }
        try child_args.append(allocator, null);

        const pid = c.fork();
        if (pid == 0) {
            _ = c.execv(sync_runner_c.ptr, @ptrCast(child_args.items.ptr));
            std.process.exit(1);
        } else if (pid > 0) {
            var status: c_int = 0;
            _ = c.waitpid(pid, &status, 0);
        }
    } else {
        std.debug.print("Unknown command: {s}\n", .{cmd});
        std.process.exit(1);
    }
}
