# Axum Extractors Module Reference (`axum::extract`)

## Tier 2: Comprehensive Extractor Specifications

Extractors parse incoming HTTP requests into type-safe Rust types.

### 1. State (`State<T>`)
- Clones internal state reference `Arc<AppState>` or inner types implementing `FromRef`.
- **Order constraint**: State extractor can appear anywhere in parameter list.

```rust
use axum::extract::{State, FromRef};

#[derive(Clone)]
pub struct AppState {
    pub db: sqlx::PgPool,
    pub api_key: String,
}

impl FromRef<AppState> for sqlx::PgPool {
    fn from_ref(state: &AppState) -> Self {
        state.db.clone()
    }
}

// Handler only extracts PgPool directly via FromRef
async fn list_users(State(pool): State<sqlx::PgPool>) -> Json<Vec<User>> { /* ... */ }
```

### 2. Path Parameters (`Path<T>`)
- Deserializes URL segments defined like `/{id}` or `/{org}/{repo}` (Axum 0.8 syntax; legacy 0.7 used `/:id`).
- Supports single primitive types `Path(id): Path<i64>` or tuples `Path((org, repo)): Path<(String, String)>` or structs `Path(params): Path<PathParams>`.

```rust
use axum::extract::Path;
use serde::Deserialize;

#[derive(Deserialize)]
pub struct ItemPath {
    pub org_id: String,
    pub item_id: i64,
}

async fn get_item(Path(params): Path<ItemPath>) -> String {
    format!("Org: {}, Item: {}", params.org_id, params.item_id)
}
```

### 3. Query Parameters (`Query<T>`)
- Deserializes URL query strings `?page=1&limit=20&search=rust`.

```rust
use axum::extract::Query;
use serde::Deserialize;

#[derive(Deserialize)]
pub struct Pagination {
    #[serde(default = "default_page")]
    pub page: usize,
    #[serde(default = "default_limit")]
    pub limit: usize,
    pub search: Option<String>,
}

fn default_page() -> usize { 1 }
fn default_limit() -> usize { 20 }

async fn search_items(Query(q): Query<Pagination>) -> Json<SearchResult> { /* ... */ }
```

### 4. JSON Payload (`Json<T>`)
- Deserializes request body into a serde struct.
- **Order rule**: `Json<T>` consumes the request body, so it MUST be the last extractor in the handler signature!

```rust
use axum::extract::Json;

async fn create_user(
    State(pool): State<AppState>, // non-consuming
    Json(payload): Json<CreateUserDto>, // consuming (MUST BE LAST)
) -> Result<Json<User>, AppError> { /* ... */ }
```
