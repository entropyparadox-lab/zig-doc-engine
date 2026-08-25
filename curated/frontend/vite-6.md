# Vite 6 Modern Frontend Build Pipeline & Configuration

## Core Features in Vite 6
- **Rolldown & Environment API**: Unified environment runtime architecture for SSR, Client, and Workers.
- **Lightning-Fast HMR**: Native ESM-based instant module replacement during local development.
- **Production Asset Pipeline**: Optimized bundle chunking, CSS code-splitting, and asset inlining thresholds.

---

## 1. Production `vite.config.ts` Pattern
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:18090',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    target: 'esnext',
    cssCodeSplit: true,
    assetsInlineLimit: 4096, // 4KB inline threshold
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },
  },
});
```

---

## 2. Environment Variables & Typing
* Client-side exposed variables must be prefixed with `VITE_`.
* Access via `import.meta.env.VITE_API_URL`.

```typescript
// vite-env.d.ts
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_APP_TITLE: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

---

## 3. Tailwind CSS v4 Integration with Vite
In Vite 6, Tailwind CSS v4 uses the `@tailwindcss/vite` plugin without requiring `postcss.config.js` or `tailwind.config.js`:

```typescript
import { defineConfig } from 'vite';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [
    tailwindcss(),
  ],
});
```
And in `src/index.css`:
```css
@import "tailwindcss";
```
