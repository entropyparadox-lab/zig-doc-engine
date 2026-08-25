# Tailwind CSS v4 Reference & Migration Guide

## Key Paradigm Changes in Tailwind v4
1. **No `tailwind.config.js`**: Replaced with CSS-first configuration via `@theme` directives in standard CSS.
2. **Lightning-fast Engine**: Built in Rust/Oxide with zero-config content detection.
3. **Single Import**: Replace `@tailwind base; @tailwind components; @tailwind utilities;` with `@import "tailwindcss";`.

## Configuration via CSS `@theme`
```css
@import "tailwindcss";

@theme {
  --font-display: "Pretendard", system-ui, sans-serif;
  --color-brand-500: oklch(0.65 0.24 250);
  --color-brand-600: oklch(0.55 0.24 250);
}
```

## Arbitrary Values & Modern CSS Features
- Container queries: `@container`, `@min-[300px]:grid-cols-2`
- Modern 3D transforms: `transform-3d`, `rotate-x-12`
- Cascade layers integrated by default.
