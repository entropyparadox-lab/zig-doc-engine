const std = @import("std");

const c = @cImport({
    @cInclude("sqlite3.h");
    @cInclude("stdio.h");
});

pub const SearchResult = struct {
    id: []const u8,
    lib_id: []const u8,
    title: []const u8,
    category: []const u8,
    version: []const u8,
    path: []const u8,
    snippet: []const u8,
};

pub const LibSummary = struct {
    lib_id: []const u8,
    category: []const u8,
    version: []const u8,
    doc_count: usize,
    total_bytes: usize,
};

pub const Engine = struct {
    allocator: std.mem.Allocator,
    db: *c.sqlite3,

    pub fn open(allocator: std.mem.Allocator, db_path_c: [:0]const u8, read_only: bool) !Engine {
        var db: ?*c.sqlite3 = null;
        const flags = if (read_only) c.SQLITE_OPEN_READONLY else (c.SQLITE_OPEN_READWRITE | c.SQLITE_OPEN_CREATE);

        if (c.sqlite3_open_v2(db_path_c, &db, flags, null) != c.SQLITE_OK) {
            return error.DbOpenFailed;
        }

        if (!read_only) {
            _ = c.sqlite3_exec(db, "PRAGMA journal_mode = WAL;", null, null, null);
            _ = c.sqlite3_exec(db, "PRAGMA synchronous = NORMAL;", null, null, null);
            _ = c.sqlite3_exec(
                db,
                \\CREATE TABLE IF NOT EXISTS docs (
                \\    id TEXT PRIMARY KEY,
                \\    lib_id TEXT NOT NULL,
                \\    title TEXT NOT NULL,
                \\    category TEXT NOT NULL,
                \\    version TEXT NOT NULL,
                \\    path TEXT NOT NULL,
                \\    content TEXT NOT NULL,
                \\    updated_at TEXT NOT NULL
                \\);
                \\CREATE INDEX IF NOT EXISTS idx_docs_lib ON docs(lib_id);
                \\CREATE INDEX IF NOT EXISTS idx_docs_ver ON docs(version);
                \\CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
                \\    id UNINDEXED,
                \\    lib_id,
                \\    title,
                \\    content,
                \\    path UNINDEXED,
                \\    tokenize = 'unicode61'
                \\);
            ,
                null,
                null,
                null,
            );
        }

        return Engine{
            .allocator = allocator,
            .db = db.?,
        };
    }

    pub fn close(self: *Engine) void {
        _ = c.sqlite3_close(self.db);
    }

    pub fn indexDocument(
        self: *Engine,
        id: []const u8,
        lib_id: []const u8,
        title: []const u8,
        category: []const u8,
        version: []const u8,
        path: []const u8,
        content: []const u8,
    ) !void {
        const sql_docs =
            \\INSERT INTO docs (id, lib_id, title, category, version, path, content, updated_at)
            \\VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, datetime('now'))
            \\ON CONFLICT(id) DO UPDATE SET
            \\   title = excluded.title,
            \\   category = excluded.category,
            \\   version = excluded.version,
            \\   path = excluded.path,
            \\   content = excluded.content,
            \\   updated_at = excluded.updated_at;
        ;

        var stmt1: ?*c.sqlite3_stmt = null;
        if (c.sqlite3_prepare_v2(self.db, sql_docs.ptr, @intCast(sql_docs.len), &stmt1, null) != c.SQLITE_OK) {
            return error.PrepareFailed;
        }
        defer _ = c.sqlite3_finalize(stmt1);

        _ = c.sqlite3_bind_text(stmt1, 1, id.ptr, @intCast(id.len), c.SQLITE_STATIC);
        _ = c.sqlite3_bind_text(stmt1, 2, lib_id.ptr, @intCast(lib_id.len), c.SQLITE_STATIC);
        _ = c.sqlite3_bind_text(stmt1, 3, title.ptr, @intCast(title.len), c.SQLITE_STATIC);
        _ = c.sqlite3_bind_text(stmt1, 4, category.ptr, @intCast(category.len), c.SQLITE_STATIC);
        _ = c.sqlite3_bind_text(stmt1, 5, version.ptr, @intCast(version.len), c.SQLITE_STATIC);
        _ = c.sqlite3_bind_text(stmt1, 6, path.ptr, @intCast(path.len), c.SQLITE_STATIC);
        _ = c.sqlite3_bind_text(stmt1, 7, content.ptr, @intCast(content.len), c.SQLITE_STATIC);

        if (c.sqlite3_step(stmt1) != c.SQLITE_DONE) {
            return error.InsertFailed;
        }

        // Update FTS
        const sql_del_fts = "DELETE FROM docs_fts WHERE id = ?1;";
        var stmt_del: ?*c.sqlite3_stmt = null;
        if (c.sqlite3_prepare_v2(self.db, sql_del_fts.ptr, @intCast(sql_del_fts.len), &stmt_del, null) == c.SQLITE_OK) {
            defer _ = c.sqlite3_finalize(stmt_del);
            _ = c.sqlite3_bind_text(stmt_del, 1, id.ptr, @intCast(id.len), c.SQLITE_STATIC);
            _ = c.sqlite3_step(stmt_del);
        }

        const sql_fts = "INSERT INTO docs_fts (id, lib_id, title, content, path) VALUES (?1, ?2, ?3, ?4, ?5);";
        var stmt2: ?*c.sqlite3_stmt = null;
        if (c.sqlite3_prepare_v2(self.db, sql_fts.ptr, @intCast(sql_fts.len), &stmt2, null) != c.SQLITE_OK) {
            return error.PrepareFailed;
        }
        defer _ = c.sqlite3_finalize(stmt2);

        _ = c.sqlite3_bind_text(stmt2, 1, id.ptr, @intCast(id.len), c.SQLITE_STATIC);
        _ = c.sqlite3_bind_text(stmt2, 2, lib_id.ptr, @intCast(lib_id.len), c.SQLITE_STATIC);
        _ = c.sqlite3_bind_text(stmt2, 3, title.ptr, @intCast(title.len), c.SQLITE_STATIC);
        _ = c.sqlite3_bind_text(stmt2, 4, content.ptr, @intCast(content.len), c.SQLITE_STATIC);
        _ = c.sqlite3_bind_text(stmt2, 5, path.ptr, @intCast(path.len), c.SQLITE_STATIC);

        if (c.sqlite3_step(stmt2) != c.SQLITE_DONE) {
            return error.InsertFailed;
        }
    }

    pub fn search(
        self: *Engine,
        sanitized_query: []const u8,
        lib_opt: ?[]const u8,
        version_opt: ?[]const u8,
        limit: usize,
    ) ![]SearchResult {
        var ver_pattern_buf: [64]u8 = undefined;
        var ver_pattern: ?[]const u8 = null;
        if (version_opt) |ver| {
            ver_pattern = std.fmt.bufPrint(&ver_pattern_buf, "{s}%", .{ver}) catch null;
        }

        var query_sql: []const u8 = undefined;
        if (lib_opt != null and ver_pattern != null) {
            query_sql =
                \\SELECT d.id, d.lib_id, d.title, d.category, d.version, d.path,
                \\       snippet(docs_fts, 3, '<b>', '</b>', '...', 25) as snip
                \\FROM docs_fts
                \\JOIN docs d ON docs_fts.id = d.id
                \\WHERE docs_fts MATCH ?1 AND d.lib_id = ?2 AND (d.version LIKE ?3 OR d.version = 'latest')
                \\ORDER BY rank
                \\LIMIT ?4;
            ;
        } else if (lib_opt != null) {
            query_sql =
                \\SELECT d.id, d.lib_id, d.title, d.category, d.version, d.path,
                \\       snippet(docs_fts, 3, '<b>', '</b>', '...', 25) as snip
                \\FROM docs_fts
                \\JOIN docs d ON docs_fts.id = d.id
                \\WHERE docs_fts MATCH ?1 AND d.lib_id = ?2
                \\ORDER BY rank
                \\LIMIT ?3;
            ;
        } else if (ver_pattern != null) {
            query_sql =
                \\SELECT d.id, d.lib_id, d.title, d.category, d.version, d.path,
                \\       snippet(docs_fts, 3, '<b>', '</b>', '...', 25) as snip
                \\FROM docs_fts
                \\JOIN docs d ON docs_fts.id = d.id
                \\WHERE docs_fts MATCH ?1 AND (d.version LIKE ?2 OR d.version = 'latest')
                \\ORDER BY rank
                \\LIMIT ?3;
            ;
        } else {
            query_sql =
                \\SELECT d.id, d.lib_id, d.title, d.category, d.version, d.path,
                \\       snippet(docs_fts, 3, '<b>', '</b>', '...', 25) as snip
                \\FROM docs_fts
                \\JOIN docs d ON docs_fts.id = d.id
                \\WHERE docs_fts MATCH ?1
                \\ORDER BY rank
                \\LIMIT ?2;
            ;
        }

        var stmt: ?*c.sqlite3_stmt = null;
        if (c.sqlite3_prepare_v2(self.db, query_sql.ptr, @intCast(query_sql.len), &stmt, null) != c.SQLITE_OK) {
            return error.PrepareFailed;
        }
        defer _ = c.sqlite3_finalize(stmt);

        _ = c.sqlite3_bind_text(stmt, 1, sanitized_query.ptr, @intCast(sanitized_query.len), c.SQLITE_STATIC);

        if (lib_opt != null and ver_pattern != null) {
            _ = c.sqlite3_bind_text(stmt, 2, lib_opt.?.ptr, @intCast(lib_opt.?.len), c.SQLITE_STATIC);
            _ = c.sqlite3_bind_text(stmt, 3, ver_pattern.?.ptr, @intCast(ver_pattern.?.len), c.SQLITE_STATIC);
            _ = c.sqlite3_bind_int64(stmt, 4, @intCast(limit));
        } else if (lib_opt != null) {
            _ = c.sqlite3_bind_text(stmt, 2, lib_opt.?.ptr, @intCast(lib_opt.?.len), c.SQLITE_STATIC);
            _ = c.sqlite3_bind_int64(stmt, 3, @intCast(limit));
        } else if (ver_pattern != null) {
            _ = c.sqlite3_bind_text(stmt, 2, ver_pattern.?.ptr, @intCast(ver_pattern.?.len), c.SQLITE_STATIC);
            _ = c.sqlite3_bind_int64(stmt, 3, @intCast(limit));
        } else {
            _ = c.sqlite3_bind_int64(stmt, 2, @intCast(limit));
        }

        var list = try std.ArrayList(SearchResult).initCapacity(self.allocator, limit);

        while (c.sqlite3_step(stmt) == c.SQLITE_ROW) {
            const id_c = c.sqlite3_column_text(stmt, 0);
            const lib_id_c = c.sqlite3_column_text(stmt, 1);
            const title_c = c.sqlite3_column_text(stmt, 2);
            const category_c = c.sqlite3_column_text(stmt, 3);
            const version_c = c.sqlite3_column_text(stmt, 4);
            const path_c = c.sqlite3_column_text(stmt, 5);
            const snip_c = c.sqlite3_column_text(stmt, 6);

            list.appendAssumeCapacity(SearchResult{
                .id = if (id_c != null) try self.allocator.dupe(u8, std.mem.span(id_c)) else "",
                .lib_id = if (lib_id_c != null) try self.allocator.dupe(u8, std.mem.span(lib_id_c)) else "",
                .title = if (title_c != null) try self.allocator.dupe(u8, std.mem.span(title_c)) else "",
                .category = if (category_c != null) try self.allocator.dupe(u8, std.mem.span(category_c)) else "",
                .version = if (version_c != null) try self.allocator.dupe(u8, std.mem.span(version_c)) else "",
                .path = if (path_c != null) try self.allocator.dupe(u8, std.mem.span(path_c)) else "",
                .snippet = if (snip_c != null) try self.allocator.dupe(u8, std.mem.span(snip_c)) else "",
            });
        }

        return list.toOwnedSlice(self.allocator);
    }

    pub fn getDocContent(self: *Engine, target: []const u8) !?[]const u8 {
        const sql = "SELECT content FROM docs WHERE id = ?1 OR path = ?1 OR lib_id = ?1 LIMIT 1;";
        var stmt: ?*c.sqlite3_stmt = null;
        if (c.sqlite3_prepare_v2(self.db, sql.ptr, @intCast(sql.len), &stmt, null) != c.SQLITE_OK) {
            return error.PrepareFailed;
        }
        defer _ = c.sqlite3_finalize(stmt);

        _ = c.sqlite3_bind_text(stmt, 1, target.ptr, @intCast(target.len), c.SQLITE_STATIC);

        if (c.sqlite3_step(stmt) == c.SQLITE_ROW) {
            const text_c = c.sqlite3_column_text(stmt, 0);
            if (text_c != null) {
                return try self.allocator.dupe(u8, std.mem.span(text_c));
            }
        }
        return null;
    }

    pub fn listLibraries(self: *Engine) ![]LibSummary {
        const sql =
            \\SELECT lib_id, category, version, COUNT(*), SUM(LENGTH(content))
            \\FROM docs
            \\GROUP BY lib_id, category, version
            \\ORDER BY category, lib_id, version;
        ;
        var stmt: ?*c.sqlite3_stmt = null;
        if (c.sqlite3_prepare_v2(self.db, sql.ptr, @intCast(sql.len), &stmt, null) != c.SQLITE_OK) {
            return error.PrepareFailed;
        }
        defer _ = c.sqlite3_finalize(stmt);

        var list: std.ArrayList(LibSummary) = .empty;

        while (c.sqlite3_step(stmt) == c.SQLITE_ROW) {
            const lib_id_c = c.sqlite3_column_text(stmt, 0);
            const cat_c = c.sqlite3_column_text(stmt, 1);
            const ver_c = c.sqlite3_column_text(stmt, 2);
            const count: usize = @intCast(c.sqlite3_column_int64(stmt, 3));
            const bytes: usize = @intCast(c.sqlite3_column_int64(stmt, 4));

            try list.append(self.allocator, LibSummary{
                .lib_id = if (lib_id_c != null) try self.allocator.dupe(u8, std.mem.span(lib_id_c)) else "",
                .category = if (cat_c != null) try self.allocator.dupe(u8, std.mem.span(cat_c)) else "",
                .version = if (ver_c != null) try self.allocator.dupe(u8, std.mem.span(ver_c)) else "",
                .doc_count = count,
                .total_bytes = bytes,
            });
        }

        return list.toOwnedSlice(self.allocator);
    }
};
