# Axum 0.7 Architecture & Routing Conventions

## Key Differences from Axum 0.8
- **Route Service vs MethodRouter**: In Axum 0.7, `Router::new().route(path, method_router)` is standard.
- **State Extractor**: Requires `#[derive(Clone)]` on AppState. Passing state via `.with_state(state)`.
- **Tower Middleware Integration**: Uses `ServiceBuilder` with standard Tower layers.

```rust
use axum::{
    extract::State,
    routing::{get, post},
    Json, Router,
};
use std::net::SocketAddr;
use tower_http::trace::TraceLayer;

#[derive(Clone)]
pub struct AppState {
    pub db: sqlx::PgPool,
}

pub fn app(state: AppState) -> Router {
    Router::new()
        .route("/health", get(|| async { "OK" }))
        .route("/items", post(create_item))
        .layer(TraceLayer::new_for_http())
        .with_state(state)
}

async fn create_item(
    State(state): State<AppState>,
    Json(payload): Json<CreateDto>,
) -> Result<Json<Item>, (axum::http::StatusCode, String)> {
    // 0.7 implementation
}

pub async fn run_server() {
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    axum::serve(listener, app(state)).await.unwrap();
}
```
