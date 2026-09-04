# Axum 0.8 Architecture & Best Practices

## Breaking Changes from Axum 0.7 to 0.8 (CRITICAL)
- **Route Path Parameter Syntax (`/{param}`)**:
  - In Axum 0.7: paths used colon prefixes (`/users/:id`, `/files/:token`).
  - In Axum 0.8: **paths MUST use braces (`/users/{id}`, `/files/{token}`)**.
  - **Wildcards**: `/*path` in 0.7 becomes `/{*path}` in 0.8.
  - **Runtime Panic if violated**:
    `Path segments must not start with ':'. For capture groups, use '{capture}'. If you meant to literally match a segment starting with a colon, call without_v07_checks on the router.`
  - **Fix**: Replace all `:param` with `{param}` in `.route()` definitions.
- **Tower-HTTP Compatibility**: Axum 0.8 requires `tower-http = "0.6"`.
- **Matchit Engine**: Upgraded to `matchit 0.8` (RFC 6570 URI template compliant).

## Core Concepts
- `axum::Router`: Type-safe route builder. Supports nesting via `.nest()` and fallback.
- `axum::extract`: Extractors for State, Path, Query, Json, and Extension.
- `axum::response::IntoResponse`: Implemented for types that can convert into HTTP responses (tuple responses `(StatusCode, Json(val))`).

## AppState Pattern
Always use `axum::extract::State` with `Arc<AppState>` or cloned internal fields:

```rust
use axum::{
    extract::{Path, State},
    routing::{get, post, delete},
    Json, Router,
};
use std::sync::Arc;

#[derive(Clone)]
pub struct AppState {
    pub db: sqlx::PgPool,
    pub config: AppConfig,
}

pub fn create_router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/health", get(health_check))
        .route("/api/items", post(create_item))
        // NOTE: Use {id} instead of :id in Axum 0.8!
        .route("/api/items/{id}", get(get_item))
        .route("/api/items/{id}", delete(delete_item))
        .with_state(state)
}

async fn health_check() -> &'static str {
    "OK"
}

async fn create_item(
    State(state): State<Arc<AppState>>,
    Json(payload): Json<CreateItemDto>,
) -> Result<Json<ItemResponse>, AppError> {
    // handler implementation
}
```

## Tower Middleware & Layers
- `tower_http::cors::CorsLayer`: Cross-origin resource sharing.
- `tower_http::trace::TraceLayer`: Tracing request/response lifecycle.
- `tower_http::compression::CompressionLayer`: Gzip/Brotli compression.

```rust
use tower_http::cors::{Any, CorsLayer};
use tower_http::trace::TraceLayer;

let app = create_router(state)
    .layer(TraceLayer::new_for_http())
    .layer(
        CorsLayer::new()
            .allow_origin(Any)
            .allow_methods(Any)
            .allow_headers(Any),
    );
```

## Error Handling Pattern (Thiserror + IntoResponse)
```rust
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    #[error("Not found: {0}")]
    NotFound(String),
    #[error("Bad request: {0}")]
    BadRequest(String),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, error_message) = match &self {
            AppError::NotFound(msg) => (StatusCode::NOT_FOUND, msg.as_str()),
            AppError::BadRequest(msg) => (StatusCode::BAD_REQUEST, msg.as_str()),
            AppError::Database(_) => (StatusCode::INTERNAL_SERVER_ERROR, "Internal server error"),
        };

        let body = Json(json!({
            "error": error_message,
            "status": status.as_u16(),
        }));

        (status, body).into_response()
    }
}
```
