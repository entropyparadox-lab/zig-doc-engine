# Tokio Synchronization Primitives Module (`tokio::sync`)

## Tier 2: Complete Channel & Locking Specifications

### 1. `mpsc` (Multi-Producer Single-Consumer)
- Bounded channel with backpressure.
- `Sender::send(item).await`: Blocks when buffer is full.
- `Receiver::recv().await`: Yields `None` when all Senders are dropped.

```rust
use tokio::sync::mpsc;

let (tx, mut rx) = mpsc::channel::<Message>(100);

tokio::spawn(async move {
    tx.send(Message::Tick).await.unwrap();
});

while let Some(msg) = rx.recv().await {
    process(msg).await;
}
```

### 2. `broadcast` (Multi-Producer Multi-Consumer)
- Each subscriber receives every message.
- Lags when slow subscribers fall behind the circular buffer capacity (`RecvError::Lagged(n)`).

```rust
use tokio::sync::broadcast;

let (tx, mut rx1) = broadcast::channel::<Event>(16);
let mut rx2 = tx.subscribe();

tx.send(Event::Reload).unwrap();

match rx1.recv().await {
    Ok(evt) => handle(evt),
    Err(broadcast::error::RecvError::Lagged(skipped)) => {
        tracing::warn!("Lagged {} messages", skipped);
    }
    Err(broadcast::error::RecvError::Closed) => {}
}
```

### 3. `watch` (Single-Value Change Notification)
- Always retains the latest single value.
- `Receiver::changed().await` notifies when a new value is published.
- `Receiver::borrow()` reads the current value synchronously without consuming it.

```rust
use tokio::sync::watch;

let (tx, mut rx) = watch::channel("initial");

tokio::spawn(async move {
    tx.send("updated_config").unwrap();
});

while rx.changed().await.is_ok() {
    let current_val = *rx.borrow();
    println!("Config updated to: {}", current_val);
}
```

### 4. `oneshot` (Single-Use Value Transfer)
- Exactly one message sent from Producer to Consumer. Commonly used for actor request-response pattern.

```rust
use tokio::sync::oneshot;

let (resp_tx, resp_rx) = oneshot::channel::<DatabaseResult>();
actor_tx.send(Command::GetUser { id: 42, respond_to: resp_tx }).await.unwrap();

let result = resp_rx.await.unwrap();
```
