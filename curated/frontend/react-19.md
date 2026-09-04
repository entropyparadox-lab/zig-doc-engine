# React 19 Core Architecture & Breaking Changes Guide

## Critical Breaking Changes (React 18 -> 19)

### 1. `ref` as a Regular Prop (Deprecation of `forwardRef`)
In React 19, function components accept `ref` directly as a prop. `React.forwardRef()` is deprecated and unnecessary.

#### ❌ Legacy React 18 (Deprecated)
```tsx
// DO NOT USE in React 19
const Input = React.forwardRef<HTMLInputElement, InputProps>((props, ref) => {
  return <input ref={ref} {...props} />;
});
```

#### ✅ Modern Fix (React 19)
```tsx
import React from 'react';

interface InputProps extends React.ComponentProps<'input'> {
  label: string;
}

export function Input({ ref, label, ...props }: InputProps) {
  return (
    <label>
      {label}
      <input ref={ref} {...props} />
    </label>
  );
}
```

---

### 2. `useActionState` (Replaces `useFormState`)
`useActionState` is exported directly from `'react'` (not `'react-dom'`) and returns an extra `isPending` boolean flag:

```tsx
import { useActionState } from 'react';

type State = { error: string | null; count: number };

async function incrementAction(prevState: State, formData: FormData): Promise<State> {
  return { error: null, count: prevState.count + 1 };
}

export function Counter() {
  const [state, formAction, isPending] = useActionState(incrementAction, { error: null, count: 0 });

  return (
    <form action={formAction}>
      <p>Count: {state.count}</p>
      <button type="submit" disabled={isPending}>
        {isPending ? 'Updating...' : 'Increment'}
      </button>
    </form>
  );
}
```

---

### 3. Context Provider Simplification (`<Context>` instead of `<Context.Provider>`)
In React 19, you can render the Context object directly as a provider without `.Provider`:

```tsx
import { createContext, useState } from 'react';

export const ThemeContext = createContext<'light' | 'dark'>('light');

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');

  // Notice: <ThemeContext value={...}> directly!
  return (
    <ThemeContext value={theme}>
      {children}
    </ThemeContext>
  );
}
```

---

### 4. Reading Async Resources with `use()`
The `use()` hook can read a Promise or Context conditionally inside render functions:

```tsx
import { use } from 'react';

export function Comments({ commentsPromise }: { commentsPromise: Promise<string[]> }) {
  // Resolves promise directly, integrating with <Suspense>
  const comments = use(commentsPromise);

  return (
    <ul>
      {comments.map((c, i) => <li key={i}>{c}</li>)}
    </ul>
  );
}
```

---

### 5. Optimistic UI Updates with `useOptimistic`
```tsx
import { useOptimistic } from 'react';

export function MessageList({ messages, sendMessage }: { messages: string[], sendMessage: (msg: string) => Promise<void> }) {
  const [optimisticMessages, addOptimisticMessage] = useOptimistic(
    messages,
    (state, newMessage: string) => [...state, `${newMessage} (sending...)`]
  );

  async function formAction(formData: FormData) {
    const text = formData.get('message') as string;
    addOptimisticMessage(text);
    await sendMessage(text);
  }

  return (
    <div>
      {optimisticMessages.map((m, i) => <div key={i}>{m}</div>)}
      <form action={formAction}>
        <input name="message" required />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
```
