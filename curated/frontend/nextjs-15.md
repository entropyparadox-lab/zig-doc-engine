# Next.js 15 App Router: Async Request APIs and Caching

Version scope: Next.js 15 App Router with React 19. Check the application's
package manifest and lockfile before applying these patterns; this is not a
recommendation to downgrade a newer Next.js application.

Source: [Official version 15 upgrade guide](https://nextjs.org/docs/app/guides/upgrading/version-15).
Adapted from PR #6, without its package-version changes.

## Async params and searchParams

Await `params` in pages, layouts, metadata functions, and route handlers.
`searchParams` is a page prop, not a layout or route-handler prop. Next.js 15
allows temporary synchronous migration access, but new code should use async APIs.

```tsx
// app/posts/[id]/page.tsx
import type { Metadata } from 'next';

type PageProps = {
  params: Promise<{ id: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
};

export default async function PostPage({ params, searchParams }: PageProps) {
  const { id } = await params;
  const { query } = await searchParams;
  const queryText = Array.isArray(query) ? query.join(', ') : query;
  return <div>Post {id}: {queryText}</div>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id } = await params;
  return { title: `Post ${id}` };
}
```

## cookies(), headers(), and draftMode()

These request APIs are asynchronous. Never render authentication cookies or
bearer tokens into HTML. Cookie presence alone does not authenticate a user;
validate the session on the server before accessing protected data.

```tsx
// app/request-info/page.tsx
import { cookies, headers, draftMode } from 'next/headers';

export default async function RequestInfo() {
  const cookieStore = await cookies();
  const headerList = await headers();
  const { isEnabled } = await draftMode();
  const locale = cookieStore.get('locale')?.value ?? 'en';
  return <div lang={locale}>
    {headerList.get('user-agent') ?? 'Unknown agent'}
    {isEnabled ? ' (draft)' : ''}
  </div>;
}
```

## Route handlers

```ts
// app/api/items/[id]/route.ts
import { NextResponse } from 'next/server';

type RouteContext = { params: Promise<{ id: string }> };

export async function GET(_request: Request, context: RouteContext) {
  const { id } = await context.params;
  return NextResponse.json({ id });
}
```

## Caching is opt-in

In Next.js 15, `fetch` requests and `GET` route handlers are no longer cached by
default. Opt in to fetch caching with `{ cache: 'force-cache' }`; for a static
`GET` handler, opt in with `export const dynamic = 'force-static'` only when the
response is safe to share. Do not globally cache user-specific authenticated data.
Uncached fetch defaults do not by themselves disable every prerendering or router
cache behavior.

For forms using React 19, import `useActionState` from `react`, not `react-dom`.
See `react-19.md` for a complete client-side example. A Server Action additionally
requires server-side authorization, input validation, and a real persistence
implementation; a client directive is not an authorization boundary.
