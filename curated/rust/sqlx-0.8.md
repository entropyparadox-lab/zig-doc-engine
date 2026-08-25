# SQLx 0.8 Best Practices & Offline Mode

## Principles
1. **Compile-time Query Verification**: Use `sqlx::query!` and `sqlx::query_as!` macros to catch SQL syntax, column name, and type mismatches during `cargo check`/`cargo build`.
2. **Offline Mode Standard**: Maintain `.sqlx/` query cache with `cargo sqlx prepare` for deterministic CI/CD and air-gapped/offline builds.

## Connection Pool Setup
```rust
use sqlx::postgres::{PgPool, PgPoolOptions};
use std::time::Duration;

pub async fn init_pool(database_url: &str) -> Result<PgPool, sqlx::Error> {
    PgPoolOptions::new()
        .max_connections(20)
        .min_connections(5)
        .acquire_timeout(Duration::from_secs(5))
        .idle_timeout(Duration::from_secs(600))
        .connect(database_url)
        .await
}
```

## Macro Queries with Type Mapping
```rust
#[derive(Debug, serde::Serialize, sqlx::FromRow)]
pub struct UserRecord {
    pub id: i64,
    pub email: String,
    pub username: String,
    pub is_active: bool,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

pub async fn find_user_by_email(pool: &PgPool, email: &str) -> Result<Option<UserRecord>, sqlx::Error> {
    sqlx::query_as!(
        UserRecord,
        r#"
        SELECT id, email, username, is_active, created_at
        FROM users
        WHERE email = $1 AND is_active = true
        LIMIT 1
        "#,
        email
    )
    .fetch_optional(pool)
    .await
}
```

## Transaction Handling
```rust
pub async fn transfer_funds(
    pool: &PgPool,
    from_id: i64,
    to_id: i64,
    amount: i64,
) -> Result<(), sqlx::Error> {
    let mut tx = pool.begin().await?;

    sqlx::query!(
        "UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1",
        amount,
        from_id
    )
    .execute(&mut *tx)
    .await?;

    sqlx::query!(
        "UPDATE accounts SET balance = balance + $1 WHERE id = $2",
        amount,
        to_id
    )
    .execute(&mut *tx)
    .await?;

    tx.commit().await?;
    Ok(())
}
```

## Offline Compilation Workflow
```bash
# 1. Start local development database
# 2. Set DATABASE_URL
export DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"

# 3. Prepare queries to update .sqlx directory
cargo sqlx prepare -- --all-targets

# 4. In CI/CD or production build (no DB connection required)
export SQLX_OFFLINE=true
cargo build --release
```
