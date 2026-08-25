# React 18 Core Conventions & Compilable Types

## React 18 Standard Action & Transition Pattern
In standard React 18 / Next.js 14, manage async form state via `useTransition` and `useState` (avoids `@types/react-dom` missing export issues):

```tsx
'use client'

import React, { useState, useTransition } from 'react';

interface FormState {
  success: boolean;
  message?: string;
}

export function ContactForm() {
  const [state, setState] = useState<FormState>({ success: false });
  const [isPending, startTransition] = useTransition();

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const name = formData.get('name') as string;

    startTransition(async () => {
      // Async server action call
      setState({ success: true, message: `Hello, ${name}` });
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="name" required />
      <button type="submit" disabled={isPending}>
        {isPending ? 'Submitting...' : 'Submit'}
      </button>
      {state.message && <p>{state.message}</p>}
    </form>
  );
}
```
