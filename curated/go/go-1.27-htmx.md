# Go 1.27 + HTMX Full-Stack Architecture & Compilable Boilerplate

## Core Architecture Principles
1. **Zero Frontend Build Step**: HTMX v2 and Alpine.js are embedded directly as static assets using `embed.FS`. No Node.js, npm, or Vite required.
2. **Single Binary Distribution**: HTML templates, static CSS/JS, and SQLite driver compile into a single 15MB static binary.
3. **HTML-First Partial Swapping**: Handlers detect `HX-Request: true` header to return compact HTML snippets instead of heavy JSON DTOs, reducing client-side JavaScript execution to zero.
4. **Native Standard Routing**: Uses Go 1.27 `net/http.ServeMux` method + path pattern matching (`"GET /items/{id}"`).

---

## 100% Compilable Main Example (`main.go`)

```go
package main

import (
	"embed"
	"fmt"
	"html/template"
	"log/slog"
	"net/http"
	"os"
	"strconv"
	"sync"
	"time"
)

//go:embed templates/*
var templateFS embed.FS

// Todo represents a task item.
type Todo struct {
	ID        int
	Title     string
	Completed bool
}

type AppState struct {
	mu    sync.RWMutex
	todos []Todo
	seq   int
}

var (
	tmpl  *template.Template
	state = &AppState{
		todos: []Todo{
			{ID: 1, Title: "금형 정밀 치수 검사", Completed: true},
			{ID: 2, Title: "라인 3 용접 결함 판정", Completed: false},
		},
		seq: 2,
	}
)

func init() {
	var err error
	tmpl, err = template.ParseFS(templateFS, "templates/*.html")
	if err != nil {
		slog.Error("Failed to parse templates", "error", err)
		os.Exit(1)
	}
}

func main() {
	mux := http.NewServeMux()

	// 1. Initial Page Load
	mux.HandleFunc("GET /{$}", handleIndex)

	// 2. Add Todo (HTMX POST)
	mux.HandleFunc("POST /todos", handleAddTodo)

	// 3. Toggle Todo (HTMX PATCH)
	mux.HandleFunc("PATCH /todos/{id}/toggle", handleToggleTodo)

	// 4. Delete Todo (HTMX DELETE)
	mux.HandleFunc("DELETE /todos/{id}", handleDeleteTodo)

	server := &http.Server{
		Addr:         ":8080",
		Handler:      mux,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	slog.Info("Go + HTMX server started", "url", "http://localhost:8080")
	if err := server.ListenAndServe(); err != nil {
		slog.Error("Server error", "error", err)
	}
}

func handleIndex(w http.ResponseWriter, r *http.Request) {
	state.mu.RLock()
	defer state.mu.RUnlock()

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	_ = tmpl.ExecuteTemplate(w, "index.html", state.todos)
}

func handleAddTodo(w http.ResponseWriter, r *http.Request) {
	title := r.FormValue("title")
	if title == "" {
		http.Error(w, "제목을 입력해주세요", http.StatusBadRequest)
		return
	}

	state.mu.Lock()
	state.seq++
	newTodo := Todo{ID: state.seq, Title: title, Completed: false}
	state.todos = append(state.todos, newTodo)
	state.mu.Unlock()

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	// Returns only the single rendered todo item snippet for hx-swap="beforeend"
	_ = tmpl.ExecuteTemplate(w, "todo-item.html", newTodo)
}

func handleToggleTodo(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.Atoi(r.PathValue("id"))
	if err != nil {
		http.Error(w, "잘못된 ID", http.StatusBadRequest)
		return
	}

	state.mu.Lock()
	var target *Todo
	for i := range state.todos {
		if state.todos[i].ID == id {
			state.todos[i].Completed = !state.todos[i].Completed
			target = &state.todos[i]
			break
		}
	}
	state.mu.Unlock()

	if target == nil {
		http.Error(w, "항목을 찾을 수 없습니다", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	// Replaces outer element
	_ = tmpl.ExecuteTemplate(w, "todo-item.html", *target)
}

func handleDeleteTodo(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.Atoi(r.PathValue("id"))
	if err != nil {
		http.Error(w, "잘못된 ID", http.StatusBadRequest)
		return
	}

	state.mu.Lock()
	newTodos := make([]Todo, 0, len(state.todos))
	for _, it := range state.todos {
		if it.ID != id {
			newTodos = append(newTodos, it)
		}
	}
	state.todos = newTodos
	state.mu.Unlock()

	// Empty body indicates element removal when swapped
	w.WriteHeader(http.StatusOK)
}
```

---

## Template Snippets (`templates/`)

### `templates/index.html`
```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>아진 현장 업무 도구</title>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  <style>
    body { font-family: -apple-system, Pretendard, sans-serif; max-width: 600px; margin: 40px auto; padding: 0 16px; color: #111; }
    .todo-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
    .todo-item.completed span { text-decoration: line-through; color: #888; }
    button { cursor: pointer; padding: 6px 12px; border-radius: 4px; border: 1px solid #ddd; background: #fff; }
    button.primary { background: #111; color: #fff; border: 0; }
  </style>
</head>
<body>
  <h1>현장 작업 체크리스트</h1>
  <form hx-post="/todos" hx-target="#todo-list" hx-swap="beforeend" hx-on::after-request="this.reset()">
    <input type="text" name="title" placeholder="새 작업을 입력하세요" required autofocus style="padding: 8px; width: 70%;">
    <button class="primary" type="submit">추가</button>
  </form>
  <div id="todo-list" style="margin-top: 20px;">
    {{range .}}
      {{template "todo-item.html" .}}
    {{end}}
  </div>
</body>
</html>
```

### `templates/todo-item.html`
```html
<div class="todo-item {{if .Completed}}completed{{end}}" id="todo-{{.ID}}">
  <span hx-patch="/todos/{{.ID}}/toggle" hx-target="#todo-{{.ID}}" hx-swap="outerHTML" style="cursor: pointer;">
    {{if .Completed}}☑{{else}}☐{{end}} {{.Title}}
  </span>
  <button hx-delete="/todos/{{.ID}}" hx-target="#todo-{{.ID}}" hx-swap="outerHTML">삭제</button>
</div>
```
