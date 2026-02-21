# React vs Next.js - Code Comparison

This guide shows the key differences between the old React + Vite setup and the new Next.js implementation.

## Routing

### React Router (Before)
```tsx
// routes.tsx
import { createBrowserRouter } from "react-router";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: HomePage },
      { path: "text-to-sign", Component: TextToSignPage },
    ],
  },
]);

// App.tsx
<RouterProvider router={router} />
```

### Next.js App Router (After)
```
src/app/
├── layout.tsx          # Replaces Layout component
├── page.tsx            # Home page (/)
├── text-to-sign/
│   └── page.tsx        # /text-to-sign route
```

File-based routing - no configuration needed!

## Navigation Links

### React Router (Before)
```tsx
import { Link } from 'react-router';

<Link to="/text-to-sign">Text to Sign</Link>
```

### Next.js (After)
```tsx
import Link from 'next/link';

<Link href="/text-to-sign">Text to Sign</Link>
```

## Getting Current Route

### React Router (Before)
```tsx
import { useLocation } from 'react-router';

const location = useLocation();
const isActive = location.pathname === '/home';
```

### Next.js (After)
```tsx
'use client';
import { usePathname } from 'next/navigation';

const pathname = usePathname();
const isActive = pathname === '/home';
```

## Layout Component

### React Router (Before)
```tsx
// Layout.tsx
import { Outlet } from 'react-router';

export function Layout() {
  return (
    <div>
      <Sidebar />
      <main>
        <Outlet /> {/* Child routes render here */}
      </main>
    </div>
  );
}
```

### Next.js (After)
```tsx
// layout.tsx
export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <Sidebar />
        <main>{children}</main>
      </body>
    </html>
  );
}
```

## Page Components

### React (Before)
```tsx
// pages/HomePage.tsx
export function HomePage() {
  return <div>Home</div>;
}
```

### Next.js (After)
```tsx
// app/page.tsx
export default function HomePage() {
  return <div>Home</div>;
}
```

## Client-Side Components

### React (Before)
```tsx
// All components are client-side by default
import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}
```

### Next.js (After)
```tsx
// Must explicitly mark as client component
'use client';

import { useState } from 'react';

export function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(count + 1)}>{count}</button>;
}
```

## Entry Point

### React + Vite (Before)
```tsx
// main.tsx
import { createRoot } from "react-dom/client";
import App from "./app/App.tsx";

createRoot(document.getElementById("root")!).render(<App />);
```

```html
<!-- index.html -->
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
```

### Next.js (After)
No entry point needed! Next.js handles this automatically.

## Configuration

### Vite (Before)
```ts
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') }
  }
})
```

### Next.js (After)
```ts
// next.config.ts
const nextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
```

## Scripts

### React + Vite (Before)
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  }
}
```

### Next.js (After)
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}
```

## Environment Variables

### React + Vite (Before)
```ts
// Access with VITE_ prefix
const apiUrl = import.meta.env.VITE_API_URL;
```

### Next.js (After)
```ts
// Public variables need NEXT_PUBLIC_ prefix
const apiUrl = process.env.NEXT_PUBLIC_API_URL;

// Server-only variables (no prefix needed)
const secret = process.env.SECRET_KEY;
```

## 404 Page

### React Router (Before)
```tsx
// routes.tsx
{ path: "*", Component: NotFound }
```

### Next.js (After)
```tsx
// app/not-found.tsx
export default function NotFound() {
  return <div>404 - Page Not Found</div>;
}
```

## Metadata

### React (Before)
```html
<!-- index.html -->
<head>
  <title>SignVista</title>
  <meta name="description" content="..." />
</head>
```

### Next.js (After)
```tsx
// layout.tsx
export const metadata = {
  title: 'SignVista',
  description: '...',
};
```

## Key Advantages of Next.js

1. **File-based Routing**: No route configuration needed
2. **Server Components**: Better performance by default
3. **Built-in Optimization**: Image optimization, code splitting
4. **SEO Friendly**: Server-side rendering support
5. **API Routes**: Can add backend endpoints easily
6. **Better DX**: Fast refresh, better error messages
7. **Production Ready**: Optimized builds out of the box

## Migration Checklist

- [x] Update package.json dependencies
- [x] Create Next.js config files
- [x] Convert routing to file-based
- [x] Update Link components
- [x] Add 'use client' directives
- [x] Update useLocation to usePathname
- [x] Create layout.tsx
- [x] Convert page components
- [x] Update imports (react-router → next/*)
- [x] Test all functionality
