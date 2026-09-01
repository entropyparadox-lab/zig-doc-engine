# Enterprise Vibe-Coding React 19 Stack Reference

## 1. Standard Enterprise Stack Matrix

| Category | Primary Choice | Key Role & Justification |
| :--- | :--- | :--- |
| **Core & Bundler** | **React 19.x + Vite 8.x (TypeScript)** | 500ms clean build, 99%+ AI generation reliability |
| **Styling & Design** | **Tailwind CSS v4 + Pretendard** | CSS-first `@theme` syntax, zero config file |
| **UI Components** | **shadcn/ui (Radix UI primitives)** | Copy & Paste headless architecture, accessible, zero lock-in |
| **Icons** | **lucide-react** | Tree-shakeable, clean SVGs, 1,000+ icons |
| **Data Grid / Table** | **@tanstack/react-table (v8) + Virtual** | Dense enterprise sorting, filtering, pagination, 100k+ rows |
| **Async Server State**| **@tanstack/react-query (v5)** | Caching, deduplication, optimistic mutations, refetching |
| **Client UI State** | **zustand (v5)** | Boilerplate-free hook store, zero context provider hell |
| **Form & Validation** | **react-hook-form + zod** | Type-safe schema validation, zero unnecessary rerenders |
| **Data Charts** | **recharts (v2.15+ with react-is override)** | Responsive SVG declarative charts (Line, Area, Bar, Pie) |
| **Toasts & Feedback** | **sonner** | Stackable, accessible, modern replacement for legacy toast |
| **AI Streaming UI** | **@ai-sdk/react** | Streaming chat (`useChat`), token completions, tools |
| **Date & Time** | **date-fns (v4)** | Modular functional date parsing, formatting, localization |

---

## 2. CRITICAL Compatibility & React 19 Guardrails

### 1) React 19 `ref` as standard prop (No `forwardRef`)
React 19 passes `ref` directly as a component prop. Do NOT wrap modern components in `React.forwardRef`:
```tsx
// ✅ React 19 Standard Component Props
export interface ButtonProps extends React.ComponentProps<'button'> {
  variant?: 'primary' | 'secondary'
}

export function Button({ variant = 'primary', className, ...props }: ButtonProps) {
  return <button className={cn('btn', variant, className)} {...props} />
}
```

### 2) Tailwind v4 & shadcn Setup
Tailwind v4 deprecates `tailwindcss-animate` in favor of `tw-animate-css` and uses `@theme` in CSS:
```css
/* app/globals.css */
@import "tailwindcss";
@import "tw-animate-css";

@theme {
  --font-sans: var(--font-pretendard), system-ui, sans-serif;
  --color-primary: var(--primary);
}
```

### 3) Recharts React 19 Package Overrides
To resolve `react-is` peer dependency conflicts with Recharts 2.x under React 19:
```json
{
  "pnpm": {
    "overrides": {
      "react-is": "19.0.0"
    }
  }
}
```

---

## 3. Core Utilities: `cn` Helper (`lib/utils.ts`)

```ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

---

## 3. Enterprise Data Grid with TanStack Table v8

```tsx
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table'
import { useState } from 'react'

interface Order {
  id: string
  client: string
  amount: number
  status: 'PAID' | 'PENDING' | 'CANCELLED'
}

export function EnterpriseDataTable({ data }: { data: Order[] }) {
  const [sorting, setSorting] = useState<SortingState>([])
  const [globalFilter, setGlobalFilter] = useState('')

  const columns: ColumnDef<Order>[] = [
    { accessorKey: 'id', header: 'Order ID' },
    { accessorKey: 'client', header: 'Client' },
    {
      accessorKey: 'amount',
      header: 'Amount',
      cell: (info) => `₩${(info.getValue() as number).toLocaleString()}`,
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: (info) => (
        <span className="px-2 py-0.5 rounded text-xs font-bold font-mono">
          {info.getValue() as string}
        </span>
      ),
    },
  ]

  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  })

  return (
    <div className="space-y-4">
      <input
        type="text"
        placeholder="Filter all columns..."
        value={globalFilter}
        onChange={(e) => setGlobalFilter(e.target.value)}
        className="px-3 py-2 border rounded-lg text-sm bg-slate-900 border-slate-700 text-white"
      />
      <div className="border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900 text-slate-400 font-mono">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    onClick={header.column.getToggleSortingHandler()}
                    className="p-3 cursor-pointer select-none"
                  >
                    {flexRender(header.column.columnDef.header, header.getContext())}
                    {{ asc: ' 🔼', desc: ' 🔽' }[header.column.getIsSorted() as string] ?? null}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-slate-800">
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="hover:bg-slate-900/50">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="p-3">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

---

## 4. Type-safe Forms with React Hook Form & Zod

```tsx
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'

const userFormSchema = z.object({
  username: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  role: z.enum(['ADMIN', 'ENGINEER', 'VIEWER']),
})

type UserFormData = z.infer<typeof userFormSchema>

export function UserCreationModal({ onClose }: { onClose: () => void }) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<UserFormData>({
    resolver: zodResolver(userFormSchema),
    defaultValues: { role: 'ENGINEER' },
  })

  const onSubmit = async (data: UserFormData) => {
    try {
      // POST API call
      toast.success(`User ${data.username} created successfully!`)
      onClose()
    } catch (err) {
      toast.error('Failed to create user')
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 p-6 bg-slate-950 rounded-2xl">
      <div>
        <label className="block text-xs text-slate-400 mb-1">Username</label>
        <input {...register('username')} className="w-full p-2 bg-slate-900 border rounded text-white" />
        {errors.username && <p className="text-red-400 text-xs mt-1">{errors.username.message}</p>}
      </div>

      <div>
        <label className="block text-xs text-slate-400 mb-1">Email</label>
        <input {...register('email')} type="email" className="w-full p-2 bg-slate-900 border rounded text-white" />
        {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email.message}</p>}
      </div>

      <button type="submit" disabled={isSubmitting} className="px-4 py-2 bg-cyan-500 text-slate-950 font-bold rounded">
        {isSubmitting ? 'Saving...' : 'Create User'}
      </button>
    </form>
  )
}
```

---

## 5. AI Chat Streaming Component (`@ai-sdk/react`)

```tsx
import { useChat } from '@ai-sdk/react'

export function ChatAssistant() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
  })

  return (
    <div className="flex flex-col h-[500px] border border-slate-800 rounded-2xl bg-slate-950 p-4">
      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`p-3 rounded-xl text-sm ${
              m.role === 'user' ? 'bg-cyan-950/60 text-cyan-200 ml-auto max-w-[80%]' : 'bg-slate-900 text-slate-200 mr-auto max-w-[80%]'
            }`}
          >
            <div className="text-[10px] font-mono text-slate-400 uppercase mb-1">{m.role}</div>
            <div className="whitespace-pre-wrap">{m.content}</div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 pt-3 border-t border-slate-800">
        <input
          value={input}
          onChange={handleInputChange}
          placeholder="Ask enterprise assistant..."
          className="flex-1 px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-400"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 bg-cyan-500 text-slate-950 font-bold rounded-xl text-xs"
        >
          Send
        </button>
      </form>
    </div>
  )
}
```
