# SolidJS 1.9+ & Modern Fine-Grained Reactivity Reference

## 1. Core Reactivity & Primitives (Fine-Grained)
SolidJS uses pure reactive graph primitives without a Virtual DOM (VDOM). Component functions execute **EXACTLY ONCE** during creation.

```tsx
import { createSignal, createMemo, createEffect, onMount, onCleanup, batch, untrack } from 'solid-js'

export function ReactiveCounter() {
  // 1. Primitive Signal: [getter, setter]
  const [count, setCount] = createSignal<number>(0)

  // 2. Computed Memo: Caches result, updates only when dependencies change
  const doubleCount = createMemo(() => count() * 2)

  // 3. Effect: Side effects tracking accessed signals
  createEffect(() => {
    console.log(`Count changed: ${count()}, Double: ${doubleCount()}`)
  })

  // 4. Lifecycle
  onMount(() => {
    console.log('Component mounted')
  })
  onCleanup(() => {
    console.log('Component disposed')
  })

  // 5. Batching updates
  const handleBatch = () => {
    batch(() => {
      setCount((c) => c + 1)
      // Multiple signal updates execute without triggering intermediate effect runs
    })
  }

  return (
    <button onClick={() => setCount((c) => c + 1)}>
      Count: {count()} / Double: {doubleCount()}
    </button>
  )
}
```

---

## 2. CRITICAL AI/LLM Pitfall: Props Destructuring is FORBIDDEN
**Never destructure props in SolidJS component parameters or bodies.** Destructuring strips getter accessors and permanently breaks reactivity.

```tsx
// ❌ WRONG: Reactivity is lost immediately!
export function BadComponent({ title, count }: { title: string; count: number }) {
  return <div>{title}: {count}</div>
}

// ✅ CORRECT: Always access via props object
export function GoodComponent(props: { title: string; count: number }) {
  return <div>{props.title}: {props.count}</div>
}
```

### Merging and Splitting Props
When defaults or rest props are needed, use `mergeProps` and `splitProps`:

```tsx
import { mergeProps, splitProps, JSX } from 'solid-js'

interface ButtonProps extends JSX.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary'
  isLoading?: boolean
  label: string
}

export function Button(rawProps: ButtonProps) {
  // 1. mergeProps: safely assigns defaults while preserving reactive getters
  const props = mergeProps({ variant: 'primary', isLoading: false }, rawProps)

  // 2. splitProps: splits into local props and HTML attributes
  const [local, others] = splitProps(props, ['variant', 'isLoading', 'label', 'class'])

  return (
    <button
      class={`btn btn-${local.variant} ${local.class || ''}`}
      disabled={local.isLoading}
      {...others}
    >
      {local.isLoading ? 'Loading...' : local.label}
    </button>
  )
}
```

---

## 3. Control Flow Components
Use built-in control flow components instead of JavaScript `.map()` or ternary expressions to prevent unnecessary DOM recreation.

```tsx
import { Show, For, Index, Switch, Match } from 'solid-js'

export function ListView(props: { items: Array<{ id: string; name: string }>; status: 'idle' | 'loading' | 'error' }) {
  return (
    <div>
      {/* 1. Show: Conditional rendering */}
      <Show when={props.items.length > 0} fallback={<p>No items found.</p>}>
        {/* 2. For: Keyed list by object reference (optimal for moving/sorting objects) */}
        <For each={props.items}>
          {(item, index) => <div>{index()}: {item.name}</div>}
        </For>
      </Show>

      {/* 3. Switch / Match: Multi-branch condition */}
      <Switch fallback={<p>Status: Unknown</p>}>
        <Match when={props.status === 'loading'}>
          <span>Loading data...</span>
        </Match>
        <Match when={props.status === 'error'}>
          <span class="text-red-500">Failed to load!</span>
        </Match>
      </Switch>
    </div>
  )
}
```

---

## 4. Deep Reactivity & Stores (`createStore`)
For nested objects and array mutations without cloning:

```tsx
import { createStore, produce } from 'solid-js/store'

interface UserState {
  profile: { name: string; email: string }
  todos: Array<{ id: number; text: string; done: boolean }>
}

export function useUserStore() {
  const [state, setState] = createStore<UserState>({
    profile: { name: 'Alice', email: 'alice@example.com' },
    todos: []
  })

  // Targeted nested update
  const updateEmail = (newEmail: string) => {
    setState('profile', 'email', newEmail)
  }

  // Immer-like mutable mutation via produce()
  const addTodo = (text: string) => {
    setState('todos', produce((todos) => {
      todos.push({ id: Date.now(), text, done: false })
    }))
  }

  return { state, updateEmail, addTodo }
}
```

---

## 5. UI Ecosystem: Kobalte & Tailwind v4

```tsx
import { DropdownMenu } from '@kobalte/core/dropdown-menu'

export function ActionMenu() {
  return (
    <DropdownMenu>
      <DropdownMenu.Trigger class="px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800">
        Options
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content class="bg-white dark:bg-slate-900 border border-slate-200 rounded-md shadow-md p-1 min-w-[160px]">
          <DropdownMenu.Item class="px-2 py-1.5 text-sm cursor-pointer rounded hover:bg-slate-100">
            Edit
          </DropdownMenu.Item>
          <DropdownMenu.Item class="px-2 py-1.5 text-sm cursor-pointer rounded text-red-600 hover:bg-red-50">
            Delete
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu>
  )
}
```
