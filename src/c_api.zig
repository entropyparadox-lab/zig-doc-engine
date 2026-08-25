const std = @import("std");
const engine = @import("engine.zig");

pub const DocEngineHandle = ?*anyopaque;

export fn doc_engine_open(db_path: [*c]const u8, read_only: bool) DocEngineHandle {
    const allocator = std.heap.c_allocator;
    const path_span = std.mem.span(db_path);
    const path_z = allocator.dupeZ(u8, path_span) catch return null;
    defer allocator.free(path_z);

    const eng = allocator.create(engine.Engine) catch return null;
    eng.* = engine.Engine.open(allocator, path_z, read_only) catch {
        allocator.destroy(eng);
        return null;
    };

    return @ptrCast(eng);
}

export fn doc_engine_close(handle: DocEngineHandle) void {
    if (handle) |ptr| {
        const eng: *engine.Engine = @ptrCast(@alignCast(ptr));
        eng.close();
        std.heap.c_allocator.destroy(eng);
    }
}

export fn doc_engine_search_json(
    handle: DocEngineHandle,
    query: [*c]const u8,
    lib_filter: [*c]const u8,
    limit: usize,
) [*c]u8 {
    if (handle == null or query == null) return null;
    const eng: *engine.Engine = @ptrCast(@alignCast(handle.?));
    const allocator = eng.allocator;

    const query_span = std.mem.span(query);
    const lib_span: ?[]const u8 = if (lib_filter != null and lib_filter[0] != 0) std.mem.span(lib_filter) else null;

    // Sanitize query
    var sanitized: std.ArrayList(u8) = .empty;
    defer sanitized.deinit(allocator);

    var iter = std.mem.tokenizeSequence(u8, query_span, " ");
    var first = true;
    while (iter.next()) |word| {
        if (!first) sanitized.append(allocator, ' ') catch return null;
        sanitized.append(allocator, '"') catch return null;
        for (word) |ch| {
            if (ch != '"') sanitized.append(allocator, ch) catch return null;
        }
        sanitized.append(allocator, '"') catch return null;
        first = false;
    }

    const results = eng.search(sanitized.items, lib_span, limit) catch return null;

    var json_buf: std.ArrayList(u8) = .empty;
    defer json_buf.deinit(allocator);

    json_buf.appendSlice(allocator, "[\n") catch return null;
    for (results, 0..) |r, idx| {
        if (idx > 0) json_buf.appendSlice(allocator, ",\n") catch return null;
        const row_str = std.fmt.allocPrint(allocator,
            \\  {{
            \\    "id": "{s}",
            \\    "lib_id": "{s}",
            \\    "title": "{s}",
            \\    "category": "{s}",
            \\    "version": "{s}",
            \\    "path": "{s}",
            \\    "snippet": "{s}"
            \\  }}
        , .{ r.id, r.lib_id, r.title, r.category, r.version, r.path, r.snippet }) catch return null;
        defer allocator.free(row_str);
        json_buf.appendSlice(allocator, row_str) catch return null;
    }
    json_buf.appendSlice(allocator, "\n]") catch return null;

    const out_z = allocator.dupeZ(u8, json_buf.items) catch return null;
    return out_z.ptr;
}

export fn doc_engine_free_string(str: [*c]u8) void {
    if (str != null) {
        const span = std.mem.span(str);
        std.heap.c_allocator.free(span);
    }
}
