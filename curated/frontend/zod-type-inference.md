# Zod v3.24+ Type-Safe Schema & Inference Idioms

## 1. Schema Definition & Inferred Types
Always derive TypeScript types from Zod schemas to maintain a single source of truth:

```typescript
import { z } from 'zod';

export const UserProfileSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  role: z.enum(['admin', 'member', 'guest']).default('member'),
  age: z.number().int().min(18).optional(),
  metadata: z.record(z.string(), z.unknown()).default({}),
  createdAt: z.coerce.date(), // Auto-converts ISO strings to Date
});

export type UserProfile = z.infer<typeof UserProfileSchema>;
```

## 2. Discriminated Unions (Polymorphic DTOs)
Use `.discriminatedUnion()` for events, messages, and state machines for optimal TypeScript narrowing:

```typescript
export const ActionEventSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('INSERT'),
    rowId: z.number(),
    payload: z.record(z.string(), z.unknown()),
  }),
  z.object({
    type: z.literal('DELETE'),
    rowId: z.number(),
    reason: z.string(),
  }),
  z.object({
    type: z.literal('PING'),
    timestamp: z.number(),
  }),
]);

export type ActionEvent = z.infer<typeof ActionEventSchema>;

function handleEvent(event: ActionEvent) {
  switch (event.type) {
    case 'INSERT':
      console.log(event.payload); // TypeScript knows payload exists
      break;
    case 'DELETE':
      console.log(event.reason); // TypeScript knows reason exists
      break;
  }
}
```

## 3. Custom Validation with `superRefine`
Use `superRefine` when field validations depend on other fields (e.g. password confirmation):

```typescript
export const SignupSchema = z
  .object({
    password: z.string().min(8),
    confirmPassword: z.string(),
  })
  .superRefine(({ password, confirmPassword }, ctx) => {
    if (confirmPassword !== password) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Passwords do not match",
        path: ["confirmPassword"],
      });
    }
  });
```

## 4. Safe Parsing in API Handlers
```typescript
export async function POST(req: Request) {
  const json = await req.json();
  const parsed = UserProfileSchema.safeParse(json);

  if (!parsed.success) {
    return Response.json(
      { error: "Validation failed", issues: parsed.error.flatten() },
      { status: 400 }
    );
  }

  const validData: UserProfile = parsed.data;
  // proceed...
}
```
