# Serde & Tracing Production Idioms in Rust

## Serde Attributes & Custom Deserialization

### Common Attributes Cheat Sheet
- `#[serde(rename_all = "camelCase")]`: For JS/TS frontend compatibility.
- `#[serde(default)]`: Fills missing fields with `Default::default()`.
- `#[serde(skip_serializing_if = "Option::is_none")]`: Omits `null` fields in JSON.
- `#[serde(flatten)]`: Inlines nested struct fields.

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ApiResponse<T> {
    pub success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<T>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "type", content = "payload", rename_all = "snake_case")]
pub enum SystemEvent {
    UserRegistered { id: i64, email: String },
    OrderPlaced { order_id: String, amount_cents: u64 },
    ShutdownRequested,
}
```

## Tracing & Structured Observability

### Subscriber Initialization
```rust
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

pub fn init_tracing() {
    tracing_subscriber::registry()
        .with(EnvFilter::try_from_default_env().unwrap_or_else(|_| "info,my_app=debug".into()))
        .with(tracing_subscriber::fmt::layer().json())
        .init();
}
```

### Instrumenting Async Functions & Spans
```rust
#[tracing::instrument(
    name = "process_payment",
    skip(payload, db_pool),
    fields(user_id = %payload.user_id, amount = payload.amount)
)]
pub async fn process_payment(payload: PaymentRequest, db_pool: &sqlx::PgPool) -> Result<PaymentReceipt, AppError> {
    tracing::debug!("Validating transaction preconditions");
    // Execution...
    tracing::info!(status = "success", "Payment finalized successfully");
    Ok(receipt)
}
```
