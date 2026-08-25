# Tailwind CSS v3 Configuration & Directives

## Core Setup in Tailwind v3
1. **JavaScript Configuration**: Requires `tailwind.config.js` or `tailwind.config.ts`.
2. **CSS Directives**: Must use three distinct directives in global CSS:
   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```
3. **Content Purging**: Explicit `content` array in `tailwind.config.js`.

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          500: "#3b82f6",
          600: "#2563eb",
        },
      },
    },
  },
  plugins: [],
}
```
