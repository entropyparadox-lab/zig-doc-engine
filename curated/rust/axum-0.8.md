# Axum 0.8 Architecture & Best Practices

## Core Concepts
- `axum::Router`: Type-safe route builder. Supports nesting via `.nest()` and fallback.
- `axum::extract`: Extractors for State, Path, Query, Json, and Extension.
- `axum::response::IntoResponse`: Implemented for types that can convert into HTTP responses (tuple responses `(StatusCode, Json(val))`).

## AppState Pattern
Always use `axum::extract::State` with `Arc<AppState>` or cloned internal fields:

```rust
use axum::{
    extract::State,
    routing::{get, post},
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
