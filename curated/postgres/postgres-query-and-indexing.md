# Postgres Query Performance & Indexing Best Practices

Comprehensive guide for AI agents and database engineers on writing high-performance queries, selecting optimal index strategies, and diagnosing query plans in PostgreSQL.

---

## 1. WHERE & JOIN Column Indexing (`query-missing-indexes`)

### Why It Matters
Unindexed columns in `WHERE`, `JOIN`, and `ORDER BY` clauses force Postgres to perform Sequential Scans (Full Table Scans), reading every page from disk/buffer cache.

### Anti-Pattern (Seq Scan)
```sql
-- Missing index on customer_id causes sequential scan of entire 10M-row orders table
SELECT id, total_amount, created_at
FROM orders
WHERE customer_id = 45120
  AND status = 'completed';
```

### Best Practice
```sql
-- Add index on filter/join predicate
CREATE INDEX idx_orders_customer_status ON orders (customer_id, status);

-- Verify execution plan changes from Seq Scan to Index Scan / Bitmap Index Scan
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, total_amount, created_at
FROM orders
WHERE customer_id = 45120
  AND status = 'completed';
```

---

## 2. Partial Indexes for Filtered Queries (`query-partial-indexes`)

### Why It Matters
When queries frequently filter on a specific subset of data (e.g., active records, unread notifications, soft-deleted rows), indexing the entire table wastes disk space, memory, and write I/O.

### Anti-Pattern
```sql
-- Full index includes 99% inactive/completed records
CREATE INDEX idx_tasks_all ON tasks (assigned_to, status);
```

### Best Practice
```sql
-- Partial index only indexes rows matching the predicate
CREATE INDEX idx_tasks_pending ON tasks (assigned_to)
WHERE status IN ('pending', 'in_progress');

-- Query matching the partial index condition exactly
SELECT id, title, priority
FROM tasks
WHERE assigned_to = 102
  AND status = 'pending';
```

---

## 3. Composite Index Column Ordering (`query-composite-indexes`)

### Why It Matters
Postgres B-tree composite indexes can only be utilized effectively if the query provides conditions starting from the leading (leftmost) column.

### Rule of Thumb
**Equality First, Range Last**: Place columns filtered with `=` or `IN` first, followed by columns filtered with ranges (`<`, `>`, `BETWEEN`, `ORDER BY`).

### Example
```sql
-- Optimal index for: WHERE tenant_id = ? AND status = ? AND created_at >= ?
CREATE INDEX idx_logs_tenant_status_created 
ON audit_logs (tenant_id, status, created_at DESC);

-- Query matching the index structure
SELECT id, action, details
FROM audit_logs
WHERE tenant_id = 'org_44a'
  AND status = 'error'
  AND created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

---

## 4. Covering Indexes with `INCLUDE` (`query-covering-indexes`)

### Why It Matters
An **Index-Only Scan** retrieves all required columns directly from the index tree without fetching heap tuples from table storage. If visibility map marks pages as all-visible, heap I/O drops to zero.

### Anti-Pattern
```sql
-- Multi-column B-tree increases index tree depth and slows writes on included data
CREATE INDEX idx_users_email_name_avatar ON users (email, display_name, avatar_url);
```

### Best Practice
```sql
-- Key columns define index structure; INCLUDE columns provide payload for Index-Only Scan
CREATE UNIQUE INDEX idx_users_email_covering ON users (email) 
INCLUDE (id, display_name, avatar_url, is_active);

-- Query performs pure Index-Only Scan
SELECT id, display_name, avatar_url, is_active
FROM users
WHERE email = 'alex@example.com';
```

---

## 5. Choosing the Right Index Type (`query-index-types`)

| Index Type | Best Used For | Operators Supported |
|---|---|---|
| **B-tree** (Default) | Scalar equality, ranges, sorting, prefix matching | `=`, `<`, `<=`, `>`, `>=`, `BETWEEN`, `IN`, `IS NULL`, `ORDER BY` |
| **GIN** (Generalized Inverted) | Multi-value data: JSONB documents, Arrays, Full-text `tsvector` | `@>`, `?`, `?&`, `?|`, `&&`, `@@` |
| **GiST** (Generalized Search Tree) | Geometric coordinates, Range types (`daterange`), Trigram similarity | `&&`, `@>`, `<@`, `~=`, `<->` (distance) |
| **BRIN** (Block Range) | Massive naturally ordered/append-only tables (Time-series, Logs) | `=`, `<`, `<=`, `>`, `>=`, `BETWEEN` (very small footprint) |

### BRIN Example for Big Time-Series Data
```sql
-- 100M-row table: BRIN index is <1MB vs B-tree >2GB
CREATE INDEX idx_sensor_data_brin ON sensor_metrics USING BRIN (recorded_at)
WITH (pages_per_range = 128);
```

---

## 6. Query Plan Diagnostics with `EXPLAIN (ANALYZE, BUFFERS)`

### Diagnostic Checklist
```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, SETTINGS)
SELECT c.name, COUNT(o.id) AS order_count
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE c.country = 'KR'
GROUP BY c.id, c.name;
```

1. **`actual rows` vs `rows` (Estimated)**: If actual differs from estimated by >10x, run `ANALYZE <table>` to refresh stale statistics.
2. **`Buffers: shared hit=... read=...`**: `hit` = read from RAM cache; `read` = fetched from NVMe/disk. Aim for >95% hits.
3. **`Rows Removed by Filter`**: High value means index didn't filter early enough; composite or partial index needed.
4. **`Sort Method: external merge Disk`**: Query exceeded `work_mem`; increase `work_mem` or add index to avoid in-memory/disk sorting.
