# Tokio Async Concurrency & Production Patterns

## Core Concurrency Primitives
- `tokio::task::JoinSet`: Bounded parallel task manager with structured concurrency.
- `tokio::sync::mpsc`: Multi-producer single-consumer channel with backpressure.
- `tokio::sync::broadcast`: Multi-producer multi-consumer publish-subscribe channel.
- `tokio::sync::watch`: Single-value change notification channel.
- `tokio::select!`: Multiplexes asynchronous operations. **Must be cancellation-safe**.

## 1. Structured Task Management with `JoinSet`
Avoid detached `tokio::spawn` for worker pools; prefer `JoinSet` to prevent memory leaks and track completion:

```rust
use tokio::task::JoinSet;

pub async fn process_batch<T: Send + 'static>(items: Vec<T>) -> Vec<ProcessResult> {
    let mut set = JoinSet::new();

    for item in items {
        set.spawn(async move {
            execute_subtask(item).await
        });
    }

    let mut results = Vec::new();
    while let Some(res) = set.join_next().await {
        match res {
            Ok(val) => results.push(val),
            Err(join_err) => {
                tracing::error!("Task panicked or cancelled: {:?}", join_err);
            }
        }
    }
    results
}
```

## 2. Cancellation-Safe `tokio::select!`
- **Safe**: `tokio::sync::mpsc::Receiver::recv`, `tokio::time::sleep`, `tokio::signal::ctrl_c`.
- **Unsafe**: `AsyncReadExt::read_exact`, custom futures holding non-idempotent state across iterations.

```rust
use tokio::sync::mpsc;
use tokio::time::{interval, Duration};

pub async fn run_event_loop(mut rx: mpsc::Receiver<Event>, mut shutdown: tokio::sync::watch::Receiver<bool>) {
    let mut ticker = interval(Duration::from_secs(30));

    loop {
        tokio::select! {
            // Biased to handle shutdown immediately
            biased;

            _ = shutdown.changed() => {
                if *shutdown.borrow() {
                    tracing::info!("Shutdown signal received. Exiting loop.");
                    break;
                }
            }
            Some(event) = rx.recv() => {
                handle_event(event).await;
            }
            _ = ticker.tick() => {
                perform_heartbeat().await;
            }
        }
    }
}
```

## 3. Production Graceful Shutdown Pattern
```rust
use tokio::signal;

pub async fn wait_for_shutdown_signal() {
    let ctrl_c = async {
        signal::ctrl_c().await.expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => tracing::info!("Received SIGINT (Ctrl+C)"),
        _ = terminate => tracing::info!("Received SIGTERM"),
    }
}
```
