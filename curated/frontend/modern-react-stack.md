# Modern React 19 & Next.js 15 Full-Stack Reference

## React 19 & Next.js 15 App Router Conventions
- **Server Components by Default**: Components without `'use client'` run purely on the server.
- **Server Actions**: Asynchronous server functions marked with `'use server'` for mutations.
- **`useActionState` & `useFormStatus`**: Native React 19 hooks for form lifecycle and optimistic feedback.

```tsx
// app/actions/items.ts
'use server'

import { revalidatePath } from 'next/cache'

export async function createItemAction(prevState: any, formData: FormData) {
  const title = formData.get('title') as string
  if (!title || title.length < 2) {
    return { error: 'Title must be at least 2 characters' }
  }

  await db.item.create({ data: { title } })
  revalidatePath('/items')
  return { success: true }
}
```

## Tailwind CSS v4 Setup
- Tailwind v4 uses CSS-first configuration via `@theme` directive in CSS instead of `tailwind.config.js`.

```css
/* app/globals.css */
@import "tailwindcss";

@theme {
  --font-sans: var(--font-pretendard), system-ui, sans-serif;
  --color-brand: #3b82f6;
}
```

## TanStack Query v5 with React 19 / Next.js
```tsx
'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

export function UserList() {
  const queryClient = useQueryClient()

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const res = await fetch('/api/users')
      if (!res.ok) throw new Error('Failed to fetch users')
      return res.json()
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  })

  const mutation = useMutation({
    mutationFn: (newUser: { name: string }) =>
      fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newUser),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  if (isLoading) return <div>Loading users...</div>

  return (
    <div>
      <ul>
        {users?.map((u: any) => (
          <li key={u.id}>{u.name}</li>
        ))}
      </ul>
      <button onClick={() => mutation.mutate({ name: 'New User' })}>Add</button>
    </div>
  )
}
```

## Zustand v5 Minimal Global State
```tsx
import { create } from 'zustand'

interface UIState {
  sidebarOpen: boolean
  toggleSidebar: () => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}))
```
