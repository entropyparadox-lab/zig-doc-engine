# Tower-HTTP 0.6 Middleware & Static Service Reference

## Core Layers & Services
- **`ServeDir`**: High-performance static file and Single Page Application (SPA) asset serving.
- **`CorsLayer`**: Configurable Cross-Origin Resource Sharing policy for REST and WebSockets.
- **`TraceLayer`**: Structured tracing via the `tracing` crate with request/response spans.
- **`CompressionLayer`**: Automatic response payload compression (gzip, brotli, zstd).
- **`TimeoutLayer`**: Enforced maximum execution duration per HTTP request.

---

## 1. ServeDir SPA & Asset Serving Pattern
```rust
use tower_http::services::ServeDir;
use axum::{Router, routing::get};
use std::path::PathBuf;

pub fn static_router(dist_dir: PathBuf) -> Router {
    Router::new()
        // Serve static bundle assets under /assets
        .nest_service("/assets", ServeDir::new(dist_dir.join("assets")))
        // Root static files with fallback to index.html for SPA routing
        .fallback_service(
            ServeDir::new(dist_dir)
                .append_index_html_on_directories(true)
        )
}
```

---

## 2. Production CORS Configuration
```rust
use tower_http::cors::{Any, CorsLayer};
use axum::http::{HeaderValue, Method};

// Permissive CORS for development / testing
pub fn dev_cors() -> CorsLayer {
    CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any)
}

// Strict CORS for production
pub fn prod_cors(origin_url: &str) -> CorsLayer {
    CorsLayer::new()
        .allow_origin(origin_url.parse::<HeaderValue>().unwrap())
        .allow_methods([Method::GET, Method::POST, Method::PUT, Method::DELETE])
        .allow_credentials(true)
}
```

---

## 3. Observability & Tracing Layer
```rust
use tower_http::trace::{TraceLayer, DefaultMakeSpan, DefaultOnResponse};
use tracing::Level;

pub fn observability_layer() -> TraceLayer<tower_http::classify::SharedClassifier<tower_http::classify::ServerErrorsAsFailures>> {
    TraceLayer::new_for_http()
        .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
        .on_response(DefaultOnResponse::new().level(Level::INFO))
}
```

---

## 4. Response Compression & Security Headers
```rust
use tower_http::compression::CompressionLayer;
use tower_http::set_header::SetResponseHeaderLayer;
use axum::http::header::{HeaderName, HeaderValue};

pub fn security_headers() -> SetResponseHeaderLayer<HeaderValue> {
    SetResponseHeaderLayer::overriding(
        HeaderName::from_static("x-content-type-options"),
        HeaderValue::from_static("nosniff"),
    )
}
```
