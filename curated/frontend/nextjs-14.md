# Next.js 14 App Router Reference

## Core Features in Next.js 14
- **App Router (`app/`)**: Default directory structure with `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`.
- **Early Server Actions**: Server Actions marked with `'use server'` inside files or inline.
- **`useFormState` Hook**: React 18 / Next 14 hook for form state (renamed to `useActionState` in React 19 / Next 15).

```tsx
// app/actions.ts
'use server'

export async function submitForm(prevState: any, formData: FormData) {
  const name = formData.get('name') as string;
  if (!name) return { error: 'Name is required' };
  return { success: true, name };
}

// app/page.tsx
'use client'

import { useFormState } from 'react-dom';
import { submitForm } from './actions';

export default function FormPage() {
  const [state, formAction] = useFormState(submitForm, null);

  return (
    <form action={formAction}>
      <input name="name" />
      <button type="submit">Submit</button>
      {state?.error && <p>{state.error}</p>}
    </form>
  );
}
```
