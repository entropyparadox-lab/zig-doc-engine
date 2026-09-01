# Svelte 5 Runes & SvelteKit 2/3 Modern Reference

## 1. Svelte 5 Runes Core (Reactivity Model)
Svelte 5 eliminates compiler-driven dirty-checking in favor of fine-grained signals known as **Runes**.

```svelte
<script lang="ts">
  // 1. $state: Reactive state
  let count = $state(0)
  let user = $state({ name: 'Alice', age: 25 })

  // 2. $state.raw: Unproxied raw state (for large immutable structures/third-party instances)
  let chartInstance = $state.raw<any>(null)

  // 3. $derived: Synchronous computed values
  let double = $derived(count * 2)

  // $derived.by: Complex multi-line derived logic
  let summary = $derived.by(() => {
    return `${user.name} has score: ${count * 10}`
  })

  // 4. $effect: Synchronous post-render side-effects
  $effect(() => {
    console.log(`Current count: ${count}`)
    return () => {
      // Cleanup runs before next effect or upon destruction
    }
  })

  // 5. $props & $bindable: Component properties
  interface Props {
    title: string
    isOpen?: boolean
    onclose?: () => void
  }
  let { title, isOpen = $bindable(false), onclose }: Props = $props()

  function increment() {
    count += 1
  }
</script>

<div class="card p-4 border rounded-lg">
  <h2 class="text-xl font-bold">{title}</h2>
  <p>Count: {count} (Double: {double})</p>
  <button onclick={increment} class="px-3 py-1 bg-blue-600 text-white rounded">
    +1
  </button>
</div>
```

---

## 2. CRITICAL AI/LLM Pitfalls: Svelte 3/4 Legacy Syntax Elimination

| Feature | ❌ Deprecated Legacy (Svelte 3/4) | ✅ Modern Svelte 5 (Runes) |
| :--- | :--- | :--- |
| **Reactive State** | `let count = 0;` (plain let in module scope) | `let count = $state(0);` |
| **Computed State** | `$: double = count * 2;` | `let double = $derived(count * 2);` |
| **Side Effects** | `$: { console.log(count); }` | `$effect(() => { console.log(count); });` |
| **Component Props**| `export let title = "Default";` | `let { title = "Default" }: Props = $props();` |
| **Event Directives**| `on:click={handleClick}` | `onclick={handleClick}` (standard DOM attribute) |
| **Slots & Children**| `<slot />`, `<slot name="header" />` | `{#snippet header()} ... {/snippet}`, `{@render header()}` |
| **App Mount (SPA)** | `new App({ target: el })` | `import { mount } from 'svelte'; mount(App, { target: el })` |
| **Icon Button A11y**| `<button onclick={...}><Icon /></button>` | `<button aria-label="Action description" onclick={...}>` (Compiler warning if omitted) |

---

## 3. Snippets and Children (`{#snippet}` & `{@render}`)
Snippets replace legacy `<slot>` tags with explicit, typed parameters.

```svelte
<!-- ChildComponent.svelte -->
<script lang="ts">
  import type { Snippet } from 'svelte'

  interface Props {
    children: Snippet
    header?: Snippet<[{ title: string }]>
  }

  let { children, header }: Props = $props()
</script>

<div class="layout">
  {#if header}
    <header class="header">
      {@render header({ title: 'Dashboard' })}
    </header>
  {/if}
  <main>
    {@render children()}
  </main>
</div>
```

---

## 4. SvelteKit 2/3 Routing & Remote Actions

### Page Server Load (`+page.server.ts`)
```ts
import type { PageServerLoad, Actions } from './$types'
import { error, fail } from '@sveltejs/kit'

export const load: PageServerLoad = async ({ params, locals, fetch }) => {
  const res = await fetch(`/api/items/${params.id}`)
  if (!res.ok) throw error(404, 'Item not found')
  const item = await res.json()
  return { item }
}

export const actions: Actions = {
  update: async ({ request }) => {
    const data = await request.formData()
    const name = data.get('name')?.toString()

    if (!name || name.length < 2) {
      return fail(400, { name, missing: true, message: 'Name must be 2+ chars' })
    }

    // Save mutation
    return { success: true }
  }
}
```

### Page Component (`+page.svelte`) with Progressive Enhancement
```svelte
<script lang="ts">
  import { enhance } from '$app/forms'
  import type { PageData, ActionData } from './$types'

  let { data, form }: { data: PageData; form: ActionData } = $props()
</script>

<h1>{data.item.name}</h1>

<form method="POST" action="?/update" use:enhance>
  <input name="name" value={form?.name ?? data.item.name} class="border p-2" />
  {#if form?.missing}
    <p class="text-red-500">{form.message}</p>
  {/if}
  <button type="submit">Update Item</button>
</form>
```
