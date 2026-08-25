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

pub fn main(init: std.process.Init) !void {
    const allocator = init.arena.allocator();

    var args_list: std.ArrayList([]const u8) = .empty;
    defer args_list.deinit(allocator);

    var it = init.minimal.args.iterate();
    while (it.next()) |arg| {
        try args_list.append(allocator, std.mem.sliceTo(arg, 0));
    }
    const args = args_list.items;

    if (args.len < 2) {
        std.debug.print(
            \\doc-engine (Zig Edition v0.16.0) - High-performance Documentation FTS5 Engine
            \\
            \\Usage:
            \\  doc-engine search <query> [--lib <lib>] [--ver <version>] [--limit <n>]
            \\  doc-engine get <id | path | lib>
            \\  doc-engine list
            \\  doc-engine index-file --lib <lib> --title <title> --path <path> [--version <ver>]
            \\  doc-engine sync [--id <source_id>]
            \\
        , .{});
        std.process.exit(1);
    }

    const cmd = args[1];

    const home = init.minimal.environ.getAlloc(allocator, "HOME") catch ".";
    const db_path = try std.fs.path.join(allocator, &[_][]const u8{ home, ".hermes", "docs", "db", "docs.db" });
    const db_path_c = try allocator.dupeZ(u8, db_path);

    if (std.mem.eql(u8, cmd, "search")) {
        var query_opt: ?[]const u8 = null;
        var lib_opt: ?[]const u8 = null;
        var ver_opt: ?[]const u8 = null;
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

        const results = try eng.search(sanitized.items, lib_opt, ver_opt, limit);

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
                \\    "path": "{s}",
                \\    "snippet": "{s}"
                \\  }}
            , .{ r.id, r.lib_id, r.title, r.category, r.version, r.path, r.snippet });
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
                \\    "doc_count": {d},
                \\    "total_bytes": {d}
                \\  }}
            , .{ item.lib_id, item.category, item.version, item.doc_count, item.total_bytes });
            defer allocator.free(item_json);
            writeFd(item_json);
        }
        writeFd("\n]\n");
    } else if (std.mem.eql(u8, cmd, "sync")) {
        const sync_script = try std.fs.path.join(allocator, &[_][]const u8{ home, ".hermes", "scripts", "sync_dev_docs_and_toolchains.py" });
        const sync_script_c = try allocator.dupeZ(u8, sync_script);

        var child_args: [3:null]?[*c]const u8 = .{
            "/usr/bin/env",
            sync_script_c.ptr,
            null,
        };

        const pid = c.fork();
        if (pid == 0) {
            _ = c.execvp("/usr/bin/env", @ptrCast(&child_args));
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
