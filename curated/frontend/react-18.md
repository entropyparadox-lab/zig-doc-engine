# React 18 Core Conventions & Hooks

## Key Patterns in React 18
- **Client-Centric Hooks**: `useState`, `useEffect`, `useCallback`, `useMemo`, `useRef`.
- **Concurrent Features**: `useTransition`, `useDeferredValue`, `Suspense`.
- **No Native Server Actions**: Mutations handled via manual `fetch` / TanStack Query, not `useActionState` or `useFormStatus` (which are React 19+ only).

```tsx
import React, { useState, useTransition } from 'react';

export function ItemList() {
  const [items, setItems] = useState<string[]>([]);
  const [isPending, startTransition] = useTransition();

  const handleAdd = (name: string) => {
    startTransition(async () => {
      const res = await fetch('/api/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      const data = await res.json();
      setItems((prev) => [...prev, data.name]);
    });
  };

  return (
    <div>
      {isPending && <p>Updating...</p>}
      <ul>{items.map((it, idx) => <li key={idx}>{it}</li>)}</ul>
    </div>
  );
}
```
