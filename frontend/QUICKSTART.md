# Quick Start Guide - Next.js Version

## Getting Started

### 1. Install Dependencies
```bash
cd SignVista/frontend
npm install
```

### 2. Run Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 3. Build for Production
```bash
npm run build
npm start
```

## Project Structure

```
SignVista/frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Home page (/)
│   │   ├── text-to-sign/
│   │   │   └── page.tsx            # Text to sign page
│   │   ├── voice-to-sign/
│   │   │   └── page.tsx            # Voice to sign page
│   │   ├── not-found.tsx           # 404 page
│   │   ├── components/             # Shared components
│   │   │   ├── Sidebar.tsx
│   │   │   ├── LoadingScreen.tsx
│   │   │   ├── Toaster.tsx
│   │   │   └── ui/                 # UI components
│   │   └── context/
│   │       └── ThemeContext.tsx    # Theme provider
│   └── styles/
│       └── index.css               # Global styles
├── public/                         # Static assets
├── next.config.ts                  # Next.js config
├── tailwind.config.ts              # Tailwind config
└── tsconfig.json                   # TypeScript config
```

## Available Scripts

- `npm run dev` - Start development server (port 3000)
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Key Features

- ✨ Next.js 15 with App Router
- 🎨 Tailwind CSS for styling
- 🌙 Dark mode support
- 🎭 GSAP animations
- 📱 Fully responsive
- ♿ Accessibility focused
- 🚀 Optimized for performance

## Development Tips

### Adding a New Page
1. Create a new folder in `src/app/`
2. Add a `page.tsx` file
3. Export a default component

Example:
```tsx
// src/app/about/page.tsx
'use client';

export default function AboutPage() {
  return <div>About Page</div>;
}
```

### Using Client Components
Add `'use client'` at the top of files that use:
- React hooks (useState, useEffect, etc.)
- Browser APIs (window, localStorage, etc.)
- Event handlers
- Third-party libraries with client-side code

### Adding Navigation Links
```tsx
import Link from 'next/link';

<Link href="/text-to-sign">Text to Sign</Link>
```

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 3000
npx kill-port 3000

# Or use a different port
npm run dev -- -p 3001
```

### Clear Next.js Cache
```bash
rm -rf .next
npm run dev
```

### Module Not Found
```bash
rm -rf node_modules package-lock.json
npm install
```

## Deployment

### Vercel (Recommended)
1. Push code to GitHub
2. Import project in Vercel
3. Deploy automatically

### Other Platforms
```bash
npm run build
npm start
```

Set `PORT` environment variable if needed.

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [GSAP](https://greensock.com/docs/)
