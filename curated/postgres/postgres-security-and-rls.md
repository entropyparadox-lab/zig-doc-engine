# Postgres Security & Row-Level Security (RLS) Best Practices

Guidelines for AI agents on designing secure multi-tenant architectures, optimizing Row-Level Security performance, applying least privilege, and writing safe database functions.

---

## 1. Multi-Tenant Row Level Security (`security-rls-basics`)

### Why It Matters
Relying solely on application-level `WHERE tenant_id = ?` clauses introduces severe security vulnerabilities. A single omitted `WHERE` clause exposes all tenants' private data. RLS enforces isolation directly in the PostgreSQL engine.

### Anti-Pattern
```sql
-- DANGEROUS: If application developer or AI agent writes:
SELECT * FROM documents;
-- ALL customer documents are leaked!
```

### Best Practice
```sql
-- 1. Enable RLS on the table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- 2. FORCE RLS so table owners / service accounts cannot bypass policies accidentally
ALTER TABLE documents FORCE ROW LEVEL SECURITY;

-- 3. Create Tenant Isolation Policy
CREATE POLICY documents_tenant_isolation ON documents
  FOR ALL
  TO authenticated
  USING (
    tenant_id = (SELECT auth.jwt() ->> 'tenant_id')::uuid
  )
  WITH CHECK (
    tenant_id = (SELECT auth.jwt() ->> 'tenant_id')::uuid
  );
```

---

## 2. Optimizing RLS Policy Performance (`security-rls-performance`)

### Why It Matters
RLS policies act as hidden `WHERE` filters injected into every `SELECT`, `UPDATE`, and `DELETE`. Unoptimized policies turn $O(\log N)$ indexed lookups into full-table scans or repeated function calls per row.

### Rule 1: Always Index Columns Referenced in RLS Policies
```sql
-- MUST INDEX: tenant_id or user_id in the policy filter
CREATE INDEX idx_documents_tenant_id ON documents (tenant_id);
```

### Rule 2: Wrap JWT/Session Functions in `(SELECT ...)` Subquery
Postgres evaluates naked functions like `auth.uid()` or `current_setting()` **once per row** if not wrapped. Wrapping in a subquery `(SELECT auth.uid())` allows the planner to treat it as an init-plan constant (evaluating **once per query**).

```sql
-- SLOW: auth.uid() called 100,000 times
CREATE POLICY profile_policy ON profiles
  FOR SELECT
  USING (user_id = auth.uid());

-- FAST: (SELECT auth.uid()) evaluated once as a constant parameter
CREATE POLICY profile_policy_optimized ON profiles
  FOR SELECT
  USING (user_id = (SELECT auth.uid()));
```

### Rule 3: Avoid Deep Joins in RLS Using Cached Metadata
```sql
-- SLOW: Policy joins 3 tables on every read
-- FAST: Denormalize tenant_id onto child table or use app-context JWT claims
CREATE POLICY memberships_policy ON team_items
  FOR SELECT
  USING (
    tenant_id = (SELECT (auth.jwt() ->> 'tenant_id')::uuid)
  );
```

---

## 3. Principle of Least Privilege & Role Separation (`security-privileges`)

### Architecture Pattern
1. **`anon` / Public**: Read-only access to public marketing/landing data.
2. **`authenticated`**: Standard user role constrained by RLS.
3. **`service_role` / Internal Admin**: High-privilege backend workers only.

### Secure Default Privileges
```sql
-- Revoke all default public execution rights
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC;

-- Grant minimal necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT SELECT ON public.public_catalog TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.user_data TO authenticated;
```

---

## 4. Secure Database Functions (`SECURITY DEFINER`)

### Why It Matters
A function declared with `SECURITY DEFINER` executes with the privileges of the function's creator (superuser/admin). If `search_path` is not explicitly pinned, an attacker can manipulate schemas to execute arbitrary code (Privilege Escalation).

### Anti-Pattern
```sql
-- INSECURE: Vulnerable to search_path hijacking
CREATE FUNCTION reset_tenant_password(user_id uuid, new_hash text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  UPDATE users SET password_hash = new_hash WHERE id = user_id;
END;
$$;
```

### Best Practice: Pin `search_path` and Revoke Public Execute
```sql
CREATE OR REPLACE FUNCTION reset_tenant_password(user_id uuid, new_hash text)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
BEGIN
  -- Strict input validation and authorization check
  IF (SELECT auth.jwt() ->> 'role') != 'super_admin' THEN
    RAISE EXCEPTION 'Access denied';
  END IF;

  UPDATE public.users 
  SET password_hash = new_hash 
  WHERE id = user_id;
END;
$$;

-- Restrict execution to authenticated backend service roles
REVOKE EXECUTE ON FUNCTION reset_tenant_password(uuid, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION reset_tenant_password(uuid, text) TO service_role;
```
