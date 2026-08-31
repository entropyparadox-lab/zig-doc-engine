# Postgres Schema Design, Migrations & Data Access Patterns

Comprehensive guide for AI agents on primary key selection, foreign key indexing, zero-downtime migrations, cursor pagination, batch loading, upsert, and JSONB/FTS optimization.

---

## 1. Primary Key Strategy (`schema-primary-keys`)

### Comparison Matrix
| Key Type | Size | Read Performance | Insert Ordering | B-Tree Bloat | Best For |
|---|---|---|---|---|---|
| `bigint generated always as identity` | 8 bytes | Ultra-fast | Sequential (append-only) | Low | Internal OLTP, High-throughput systems |
| `UUID v7` (Time-ordered) | 16 bytes | Fast | Sequential (time-sorted) | Low | Distributed microservices, Client-generated IDs |
| `UUID v4` (Random) | 16 bytes | Slower | Random | High (Leaf Splitting) | Cryptographic security where order must be obscured |

### Best Practice (Postgres 17+ or Extension / UUIDv7)
```sql
-- Pattern A: Identity (High-performance single-DB)
CREATE TABLE users (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email text NOT NULL UNIQUE
);

-- Pattern B: UUIDv7 (Time-ordered 128-bit ID for distributed systems)
CREATE TABLE orders (
  id uuid PRIMARY KEY DEFAULT uuidv7(),
  created_at timestamptz NOT NULL DEFAULT now()
);
```

---

## 2. Foreign Key Indexing (`schema-foreign-key-indexes`)

### Why It Matters
PostgreSQL **does not automatically index foreign key columns**. If unindexed:
1. `JOIN` queries perform Sequential Scans on the child table.
2. `DELETE` or `UPDATE` on the parent table takes a full table share lock or sequential scan on the child table to verify referential integrity.

### Best Practice
```sql
CREATE TABLE authors (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name text NOT NULL
);

CREATE TABLE books (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  author_id bigint NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
  title text NOT NULL
);

-- CRITICAL: Always index the foreign key
CREATE INDEX idx_books_author_id ON books (author_id);
```

---

## 3. Safe Zero-Downtime Constraints (`schema-constraints`)

### Why It Matters
Adding a `CHECK` or `FOREIGN KEY` constraint directly on a large production table holds an `ACCESS EXCLUSIVE` lock while validating all existing rows, causing application outages.

### Safe 2-Step Migration Pattern
```sql
-- Step 1: Add constraint with NOT VALID (instantly acquires lock and checks only new writes)
ALTER TABLE orders 
ADD CONSTRAINT check_positive_amount 
CHECK (amount > 0) NOT VALID;

-- Step 2: Validate existing rows in background (takes SHARE UPDATE EXCLUSIVE lock without blocking reads/writes)
ALTER TABLE orders 
VALIDATE CONSTRAINT check_positive_amount;
```

---

## 4. Cursor / Keyset-Based Pagination vs OFFSET (`data-pagination`)

### Why It Matters
`OFFSET 100000 LIMIT 20` forces Postgres to compute, sort, and discard 100,000 rows ($O(N)$ CPU & Memory waste). Keyset pagination uses indexed B-tree lookups ($O(\log N)$).

### Anti-Pattern
```sql
-- Slow: scans and drops 50,000 rows
SELECT id, title, created_at
FROM posts
ORDER BY created_at DESC, id DESC
LIMIT 20 OFFSET 50000;
```

### Best Practice: Keyset / Cursor Pagination
```sql
-- Fast: Index-seek directly to next page
-- Composite index: (created_at DESC, id DESC)
SELECT id, title, created_at
FROM posts
WHERE (created_at, id) < ($last_seen_created_at, $last_seen_id)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

---

## 5. Batch Inserts & Atomic UPSERT (`data-batch-inserts`, `data-upsert`)

### Batch Inserts
```sql
-- Multi-row insert (up to 1,000 rows per statement)
INSERT INTO metrics (device_id, cpu_usage, memory_usage, recorded_at)
VALUES 
  ('dev_1', 45.2, 78.1, NOW()),
  ('dev_2', 12.8, 34.0, NOW()),
  ('dev_3', 88.5, 91.2, NOW());
```

### Atomic UPSERT (`ON CONFLICT`)
```sql
INSERT INTO user_daily_stats (user_id, stat_date, login_count, total_spent)
VALUES (104, '2026-08-26', 1, 45000)
ON CONFLICT (user_id, stat_date)
DO UPDATE SET 
  login_count = user_daily_stats.login_count + EXCLUDED.login_count,
  total_spent = user_daily_stats.total_spent + EXCLUDED.total_spent,
  updated_at = NOW();
```

---

## 6. Eliminating N+1 Queries with Single-Query Aggregation (`data-n-plus-one`)

### Anti-Pattern
Querying parent items, then looping in Python/TypeScript to execute 1 query per child item.

### Best Practice: `json_agg` / `jsonb_agg` Subquery
```sql
SELECT 
  u.id, 
  u.email,
  COALESCE(
    (
      SELECT jsonb_agg(
        jsonb_build_object(
          'id', o.id,
          'amount', o.amount,
          'status', o.status
        ) ORDER BY o.created_at DESC
      )
      FROM orders o
      WHERE o.user_id = u.id
    ), '[]'::jsonb
  ) AS recent_orders
FROM users u
WHERE u.is_active = true
LIMIT 50;
```

---

## 7. JSONB GIN Indexing & Full-Text Search (`advanced-jsonb-indexing`, `advanced-full-text-search`)

### JSONB GIN Indexing
```sql
-- jsonb_path_ops is 30-50% smaller and faster for @> containment queries
CREATE INDEX idx_events_payload_gin ON events USING GIN (payload jsonb_path_ops);

-- Fast containment query
SELECT id, event_type
FROM events
WHERE payload @> '{"status": "failed", "retry_count": 3}';
```

### Generated Column Full-Text Search
```sql
-- Generated tsvector column updated automatically
ALTER TABLE articles 
ADD COLUMN search_vector tsvector 
GENERATED ALWAYS AS (
  to_tsvector('english', coalesce(title, '') || ' ' || coalesce(body, ''))
) STORED;

CREATE INDEX idx_articles_search ON articles USING GIN (search_vector);

-- Fast text query
SELECT id, title, ts_rank(search_vector, query) as rank
FROM articles, websearch_to_tsquery('english', 'postgres performance indexing') query
WHERE search_vector @@ query
ORDER BY rank DESC
LIMIT 20;
```
