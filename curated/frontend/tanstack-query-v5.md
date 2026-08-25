# TanStack Query v5 Reference & Migration Guide

## Key Changes in v5
1. **Single Object Argument**: All queries and mutations now take a single configuration object:
   - `useQuery({ queryKey, queryFn, ... })`
   - `useMutation({ mutationFn, ... })`
2. **Simplified Statuses**: `isLoading` is deprecated; use `isPending` for query running without cached data.
3. **Suspense Hooks**: Dedicated `useSuspenseQuery`, `useSuspenseQueries`, and `useSuspenseInfiniteQuery`.

## Standard Patterns
```tsx
import { useQuery, useMutation, useQueryClient, useSuspenseQuery } from '@tanstack/react-query';

export const userKeys = {
  all: ['users'] as const,
  detail: (id: string) => ['users', id] as const,
};

// 1. Basic Query
export function useUser(id: string) {
  return useQuery({
    queryKey: userKeys.detail(id),
    queryFn: async () => {
      const res = await fetch(`/api/users/${id}`);
      if (!res.ok) throw new Error('Network error');
      return res.json();
    },
    staleTime: 1000 * 60 * 5, // 5 min
    gcTime: 1000 * 60 * 30, // 30 min (replaces cacheTime)
  });
}

// 2. Suspense Query for React 19 / Server Components
export function useUserSuspense(id: string) {
  return useSuspenseQuery({
    queryKey: userKeys.detail(id),
    queryFn: async () => {
      const res = await fetch(`/api/users/${id}`);
      return res.json();
    },
  });
}

// 3. Mutation with Invalidation
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: { id: string; name: string }) => {
      const res = await fetch(`/api/users/${data.id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
      return res.json();
    },
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: userKeys.all });
      queryClient.setQueryData(userKeys.detail(updated.id), updated);
    },
  });
}
```
