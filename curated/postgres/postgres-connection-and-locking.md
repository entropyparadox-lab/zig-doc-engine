# Postgres Connection Management, Concurrency & Locking Best Practices

Guidelines for AI agents and backend architects on connection pooling, transaction lifecycles, deadlock avoidance, message queues (`SKIP LOCKED`), and advisory locks.

---

## 1. Connection Pooling (`conn-pooling`, `conn-limits`)

### Why It Matters
PostgreSQL uses a process-per-connection model. Each connection allocates 5–10MB of memory and causes CPU context switching under high load. Direct unpooled connections from serverless or AI agents will exhaust backend limits.

### Architecture Rules
1. **Always Use a Pooler**: Use PgBouncer or Supavisor in **Transaction Mode** for stateless web apps and serverless lambdas.
2. **Sizing Formula**:
   $$\text{max\_connections} \approx (\text{CPU Cores} \times 2) + \text{Effective Spindle Count}$$
   Example: On an 8-core DB server, a pool of 20–30 active connections provides higher throughput than 500 unmanaged connections.

### Prepared Statements with Transaction Pooling (`conn-prepared-statements`)
In PgBouncer transaction pooling mode, named prepared statements can leak across clients.
- **Node/TypeScript (pg/drizzle/prisma)**: Use unnamed/anonymous prepared statements or set `prepare: false`.
- **Rust (sqlx)**: Ensure PgBouncer compatibility by setting `statement_cache_capacity(0)` when using transaction mode poolers.

---

## 2. Idle Connection Timeouts (`conn-idle-timeout`)

### Why It Matters
Orphaned transactions hold locks, prevent `VACUUM` from cleaning dead tuples (leading to table bloat), and exhaust connection pools.

### Recommended Postgres Settings
```sql
-- Terminate transactions left open and idle for more than 15 seconds
ALTER SYSTEM SET idle_in_transaction_session_timeout = '15s';

-- Terminate idle client connections after 10 minutes
ALTER SYSTEM SET idle_session_timeout = '10min';

-- Terminate any single query running longer than 30 seconds (OLTP default)
ALTER SYSTEM SET statement_timeout = '30s';

-- Reload configuration
SELECT pg_reload_conf();
```

---

## 3. Keep Transactions Short (`lock-short-transactions`)

### Anti-Pattern: External I/O inside DB Transaction
```typescript
// BAD: Transaction holds database lock while awaiting third-party HTTP call
await db.transaction(async (tx) => {
  const user = await tx.users.findById(userId);
  
  // NEVER DO THIS: 2000ms network delay holds lock on user row
  const paymentResult = await stripe.charges.create({ amount: 5000 });
  
  await tx.orders.create({ userId, chargeId: paymentResult.id });
});
```

### Best Practice: Prepare -> Call External API -> Commit
```typescript
// GOOD: Perform network I/O outside DB transaction
const reservation = await db.orders.createPending({ userId, amount: 5000 });

const paymentResult = await stripe.charges.create({ 
  amount: 5000, 
  idempotencyKey: reservation.id 
});

await db.orders.markPaid({ id: reservation.id, chargeId: paymentResult.id });
```

---

## 4. Deadlock Prevention via Consistent Lock Ordering (`lock-deadlock-prevention`)

### Why It Matters
A deadlock occurs when Transaction A locks Row 1 and attempts to lock Row 2, while Transaction B locks Row 2 and attempts to lock Row 1.

### Anti-Pattern
Updating multiple rows in arbitrary or incoming payload order.

### Best Practice: Sort Primary Keys Before Locking
```sql
-- Always sort IDs in ascending order before performing batch updates or SELECT FOR UPDATE
BEGIN;

-- Sort IDs deterministically: [101, 105, 109]
SELECT id, balance 
FROM accounts 
WHERE id IN (105, 101, 109)
ORDER BY id ASC
FOR UPDATE;

UPDATE accounts SET balance = balance - 100 WHERE id = 101;
UPDATE accounts SET balance = balance + 100 WHERE id = 105;

COMMIT;
```

---

## 5. Non-Blocking Job Queues with `FOR UPDATE SKIP LOCKED` (`lock-skip-locked`)

### Why It Matters
When multiple worker agents process tasks from a database table, standard `SELECT FOR UPDATE` causes workers to block each other. `SKIP LOCKED` allows workers to instantly grab the next unreserved task.

### High-Throughput Queue Pattern
```sql
-- Worker query: atomically claim 10 pending jobs without waiting on other workers
WITH next_jobs AS (
  SELECT id
  FROM background_jobs
  WHERE status = 'pending'
    AND scheduled_at <= NOW()
  ORDER BY priority DESC, id ASC
  LIMIT 10
  FOR UPDATE SKIP LOCKED
)
UPDATE background_jobs
SET status = 'processing',
    locked_by = 'worker_agent_03',
    started_at = NOW(),
    attempts = attempts + 1
WHERE id IN (SELECT id FROM next_jobs)
RETURNING id, task_type, payload;
```

---

## 6. Application-Level Distributed Locks with Advisory Locks (`lock-advisory`)

### Why It Matters
Postgres Advisory Locks provide fast, lightweight application mutexes (in RAM) without creating lock contention on actual data rows or tables.

### Session vs Transaction Advisory Locks
```sql
-- Transaction-scoped advisory lock (auto-releases on COMMIT or ROLLBACK)
BEGIN;

-- Hash of the resource name or integer ID
SELECT pg_advisory_xact_lock(hashtext('daily_settlement_reconciliation_2026_08_26'));

-- Critical section: only ONE agent/process can execute this concurrently
PERFORM run_daily_settlement();

COMMIT; -- Lock is automatically released here

-- Try lock (non-blocking: returns true if acquired, false immediately if busy)
SELECT pg_try_advisory_xact_lock(10042);
```
