# Tokio 1.43 Asynchronous Runtime & Concurrency Best Practices

## Core Concepts
- **Multi-Threaded Runtime**: `#[tokio::main]` initializes a work-stealing thread pool optimized for high-throughput I/O.
- **Task Spawning**: `tokio::spawn` creates cooperative green threads. All spawned tasks must be `'static + Send`.
- **JoinSet**: `tokio::task::JoinSet` manages a dynamic pool of concurrent async tasks with structured cancellation and completion draining.

---

## 1. Task Spawning & Structured JoinSet
```rust
use tokio::task::JoinSet;

pub async fn run_batch_jobs(items: Vec<String>) -> Vec<Result<String, String>> {
    let mut set = JoinSet::new();

    for item in items {
        set.spawn(async move {
            // Async I/O or RPC processing
            tokio::time::sleep(tokio::time::Duration::from_millis(50)).await;
            format!("Processed {}", item)
        });
    }

    let mut results = Vec::new();
    while let Some(res) = set.join_next().await {
        match res {
            Ok(output) => results.push(Ok(output)),
            Err(join_err) => results.push(Err(join_err.to_string())),
        }
    }
    results
}
```

---

## 2. Synchronization Channels (`tokio::sync`)
* `mpsc`: Multi-Producer Single-Consumer (bounded channel with backpressure).
* `broadcast`: Multi-Producer Multi-Consumer (pub/sub for real-time WebSocket events).
* `watch`: Single-Producer Multi-Consumer (state change notification, keeps latest value).
* `oneshot`: Single-Producer Single-Consumer (one-off request-response pair).

```rust
use tokio::sync::{mpsc, watch};

#[derive(Clone, Debug)]
pub struct Event(pub String);

// MPSC bounded channel with backpressure
let (tx, mut rx) = mpsc::channel::<Event>(100);

tokio::spawn(async move {
    tx.send(Event("job_started".into())).await.unwrap();
});

while let Some(evt) = rx.recv().await {
    println!("Received: {:?}", evt);
}

// Watch channel for shutdown signal
let (shutdown_tx, mut shutdown_rx) = watch::channel(false);
tokio::spawn(async move {
    while shutdown_rx.changed().await.is_ok() {
        if *shutdown_rx.borrow() {
            println!("Graceful shutdown triggered");
            break;
        }
    }
});
```

---

## 3. Timeouts & Select Pattern
Use `tokio::select!` for racing multiple async operations or attaching bounded timeouts:

```rust
use tokio::time::{timeout, Duration};

async fn fetch_with_deadline() -> Result<String, &'static str> {
    let job = async {
        tokio::time::sleep(Duration::from_millis(200)).await;
        "Success"
    };

    match timeout(Duration::from_millis(500), job).await {
        Ok(val) => Ok(val),
        Err(_) => Err("Timeout exceeded"),
    }
}
```

---

## 4. Graceful Shutdown Signal Pattern (Axum / Server Daemon)
```rust
pub async fn shutdown_signal() {
    let ctrl_c = async {
        tokio::signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }
}
```
