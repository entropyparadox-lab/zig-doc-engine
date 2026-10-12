# Go 1.27 Standard Library Reference & Complete Compilable Idioms

## Core v1.27+ Breaking Changes & Invariants
- **Enhanced `net/http.ServeMux` Routing**:
  - Direct HTTP method matching: `"GET /items/{id}"`, `"POST /items"`, `"DELETE /items/{id}"`.
  - Path wildcards: `{id}` captures single path segment; `{path...}` captures remainder of path.
  - Exact root/suffix matching: `"/{$}"` matches only `/` without matching sub-paths.
  - Path value extraction: `r.PathValue("id")` (replaces third-party Gorilla Mux `mux.Vars` and Chi `chi.URLParam`).
- **Generalized Function Type Inference (Go 1.27 Specification)**:
  - Function type arguments can now be omitted in all assignment contexts, channel sends, type conversions, and composite literals.
  - Generic helper functions like `Map(slice, fn)` or `Filter(slice, predicate)` can be assigned or invoked without explicit type parameter instantiation (`Map(items, f)` instead of `Map[int, string](items, f)`).
- **Structured Logging (`log/slog`)**:
  - Use standard `slog.Default()` or `slog.New(slog.NewJSONHandler(os.Stdout, nil))`.
- **Embedded Assets (`embed.FS`)**:
  - Embed HTML templates, CSS, and JS directly into the binary: `//go:embed static/* templates/*`.
- **Zero External Dependencies**:
  - Avoid third-party routers (`chi`, `gin`, `fiber`, `mux`) when building microservices; standard `net/http` provides native high-performance routing.

---

## 100% Compilable Main Example (Go 1.27)

```go
package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"sync"
	"syscall"
	"time"
)

// Item represents a domain entity.
type Item struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

// Store provides thread-safe in-memory item storage.
type Store struct {
	mu    sync.RWMutex
	items map[int]Item
	seq   int
}

func NewStore() *Store {
	return &Store{
		items: make(map[int]Item),
	}
}

// Generic Map utilizing Go 1.27 generalized function type inference.
func Map[T any, R any](in []T, fn func(T) R) []R {
	out := make([]R, len(in))
	for i, v := range in {
		out[i] = fn(v)
	}
	return out
}

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	slog.SetDefault(logger)

	store := NewStore()
	mux := http.NewServeMux()

	// Exact root match using {$} pattern
	mux.HandleFunc("GET /{$}", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_ = json.NewEncoder(w).Encode(map[string]string{
			"status":  "ok",
			"service": "go-1.27-api",
		})
	})

	// List items
	mux.HandleFunc("GET /items", func(w http.ResponseWriter, r *http.Request) {
		store.mu.RLock()
		defer store.mu.RUnlock()

		list := make([]Item, 0, len(store.items))
		for _, item := range store.items {
			list = append(list, item)
		}

		// Go 1.27: function type inference in assignment without explicit [Item, string]
		names := Map(list, func(it Item) string {
			return it.Name
		})

		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_ = json.NewEncoder(w).Encode(map[string]any{
			"count": len(list),
			"items": list,
			"names": names,
		})
	})

	// Get single item with {id} wildcard and r.PathValue
	mux.HandleFunc("GET /items/{id}", func(w http.ResponseWriter, r *http.Request) {
		idStr := r.PathValue("id")
		id, err := strconv.Atoi(idStr)
		if err != nil {
			http.Error(w, "invalid id parameter", http.StatusBadRequest)
			return
		}

		store.mu.RLock()
		item, exists := store.items[id]
		store.mu.RUnlock()

		if !exists {
			http.Error(w, "item not found", http.StatusNotFound)
			return
		}

		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_ = json.NewEncoder(w).Encode(item)
	})

	// Create item
	mux.HandleFunc("POST /items", func(w http.ResponseWriter, r *http.Request) {
		var req struct {
			Name string `json:"name"`
		}
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "invalid json payload", http.StatusBadRequest)
			return
		}
		if req.Name == "" {
			http.Error(w, "name cannot be empty", http.StatusUnprocessableEntity)
			return
		}

		store.mu.Lock()
		store.seq++
		item := Item{ID: store.seq, Name: req.Name}
		store.items[item.ID] = item
		store.mu.Unlock()

		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.WriteHeader(http.StatusCreated)
		_ = json.NewEncoder(w).Encode(item)
	})

	server := &http.Server{
		Addr:         ":8080",
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful shutdown
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	go func() {
		slog.Info("Server listening", "addr", server.Addr)
		if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			slog.Error("Server listen failure", "error", err)
			os.Exit(1)
		}
	}()

	<-stop
	slog.Info("Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		slog.Error("Server forced shutdown", "error", err)
	} else {
		slog.Info("Server stopped cleanly")
	}
}
```

---

## Anti-Pattern Defense
| Anti-Pattern | Correct Go 1.27 Idiom | Why |
| :--- | :--- | :--- |
| `import "github.com/gorilla/mux"` | `mux.HandleFunc("GET /items/{id}", ...)` | `gorilla/mux` is archived; `net/http` provides native sub-microsecond path routing. |
| `chi.URLParam(r, "id")` | `r.PathValue("id")` | Standard library zero-dependency method. |
| `Map[int, string](items, f)` | `Map(items, f)` | Go 1.27 generalized function type inference deduces `T` and `R` automatically. |
| `log.Println(...)` | `slog.Info("message", "key", val)` | Structured JSON/text logging with context propagation. |
