# Next.js 15 Modern Architecture & Breaking Changes Guide

## Critical Breaking Changes (Next.js 14 -> 15)

### 1. Async Request APIs (`params` & `searchParams` are now Promises)
In Next.js 15, `params` and `searchParams` passed to pages, layouts, metadata resolvers, and route handlers are **asynchronous Promises**.

#### ❌ Error Symptom (LLM Hallucination from Next.js 14)
```text
Error: Route "/posts/[id]" used `params.id`. `params` should be awaited before using its properties.
Learn more: https://nextjs.org/docs/messages/sync-dynamic-apis
```

#### ✅ Modern Fix (Next.js 15)
```tsx
// app/posts/[id]/page.tsx
type PageProps = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
};

export default async function PostPage({ params, searchParams }: PageProps) {
  const { id } = await params;
  const { query } = await searchParams;

  return <div>Post ID: {id} (Query: {query})</div>;
}

// Generate Metadata
export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return { title: `Post ${id}` };
}
```

---

### 2. Async `cookies()` and `headers()`
In Next.js 15, `cookies()` and `headers()` from `next/headers` must be explicitly `await`ed.

#### ❌ Error Symptom
```text
Error: `cookies()` should be awaited before using its properties.
```

#### ✅ Modern Fix (Next.js 15)
```tsx
import { cookies, headers } from 'next/headers';

export async function AuthProfile() {
  const cookieStore = await cookies();
  const token = cookieStore.get('auth_token')?.value;

  const headerList = await headers();
  const userAgent = headerList.get('user-agent');

  return <div>User Token: {token}</div>;
}
```

---

### 3. Fetch Caching Inversion (`no-store` by default)
* **Next.js 14**: `fetch` cached `force-cache` by default.
* **Next.js 15**: `fetch` requests default to **`no-store` (uncached)**.
* To opt into caching in Next.js 15:
  ```ts
  // Explicitly opt into caching
  const res = await fetch('https://api.example.com/data', { cache: 'force-cache' });
  ```

---

### 4. Route Handlers in Next.js 15
Dynamic route handler contexts also require `await context.params`:

```ts
// app/api/items/[id]/route.ts
import { NextResponse, type NextRequest } from 'next/server';

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function GET(request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  return NextResponse.json({ id, status: 'active' });
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  const { id } = await context.params;
  return NextResponse.json({ deleted: id });
}
```

---

### 5. Server Actions with React 19 (`useActionState`)
In Next.js 15 / React 19, use `useActionState` from `react` (replaces deprecated `useFormState` from `react-dom`):

```tsx
'use client'

import { useActionState } from 'react';
import { updateProfileAction } from './actions';

export function ProfileForm() {
  const [state, formAction, isPending] = useActionState(updateProfileAction, { error: null });

  return (
    <form action={formAction}>
      <input name="username" required />
      <button type="submit" disabled={isPending}>
        {isPending ? 'Saving...' : 'Save Profile'}
      </button>
      {state.error && <p className="text-red-500">{state.error}</p>}
    </form>
  );
}
```
