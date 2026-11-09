# React 19: Refs, Actions, Context, and Async Resources

Version scope: React 19 with matching React DOM and TypeScript types. Inspect the
consumer's lockfile before using these APIs; React 18 does not support them all.
Source: [Official React 19 release](https://react.dev/blog/2024/12/05/react-19).
Adapted from PR #6, without its package-version changes.

## ref as a prop

React 19 function components can accept `ref` as a normal prop. `forwardRef` is
no longer necessary for new React 19-only components, but remains available for
compatibility; it was not removed in React 19. Libraries supporting React 18
still need a compatible ref-forwarding strategy.

```tsx
import type { ComponentProps } from 'react';

type InputProps = ComponentProps<'input'> & { label: string };

export function Input({ ref, label, ...props }: InputProps) {
  return <label>{label}<input ref={ref} {...props} /></label>;
}
```

## useActionState replaces useFormState

Import `useActionState` from `react`. Its result is `[state, formAction, isPending]`.
The action receives the previous state before the submitted payload. Pass the
wrapped action to `<form action>` to establish the Action/Transition context.
This example is local UI state, not a Server Action or database mutation.

```tsx
'use client';

import { useActionState } from 'react';

type State = { error: string | null; count: number };

async function incrementAction(previous: State, _data: FormData): Promise<State> {
  return { error: null, count: previous.count + 1 };
}

export function Counter() {
  const initialState: State = { error: null, count: 0 };
  const [state, formAction, isPending] = useActionState(incrementAction, initialState);
  return <form action={formAction}>
    <p>Count: {state.count}</p>
    <button type="submit" disabled={isPending}>Increment</button>
    {state.error && <p role="alert">{state.error}</p>}
  </form>;
}
```

## Context providers

React 19 supports `<ThemeContext value={...}>`; the older `.Provider` form still
works. Use explicit imports for types rather than depending on a global namespace.

```tsx
'use client';

import { createContext, useState, type ReactNode } from 'react';

export const ThemeContext = createContext<'light' | 'dark'>('light');

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme] = useState<'light' | 'dark'>('dark');
  return <ThemeContext value={theme}>{children}</ThemeContext>;
}
```

## use() and useOptimistic

`use()` reads a Promise or context during render and may be called conditionally
inside a component or custom hook. A pending Promise suspends; use a Suspense
boundary and an Error Boundary for rejection handling. Pass a stable Promise
from a framework/cache or Server Component, not a fresh Promise created on each
client render.

```tsx
'use client';

import { Suspense, use } from 'react';

type Comment = { id: string; text: string };

function Comments({ resource }: { resource: Promise<Comment[]> }) {
  const comments = use(resource);
  return <ul>{comments.map(comment => <li key={comment.id}>{comment.text}</li>)}</ul>;
}

export function CommentsPanel({ resource }: { resource: Promise<Comment[]> }) {
  return <Suspense fallback={<p>Loading...</p>}><Comments resource={resource} /></Suspense>;
}
```

`useOptimistic` maintains temporary UI during an Action. Call its update function
inside an Action/Transition, then update the authoritative state when persistence
succeeds; optimistic state is not a substitute for saving data. Surface failures
and retain the authoritative state rather than silently reporting success.
