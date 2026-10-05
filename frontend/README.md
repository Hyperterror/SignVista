# SignVista Frontend

Next.js 15 (App Router) + Tailwind CSS. See the [root README](../README.md)
for setup.

## How it talks to the backend

- `next.config.ts` proxies `/api/*`, `/assets/signs/*` and `/health` to
  `BACKEND_URL` (default `http://127.0.0.1:8000`). The browser only uses the
  frontend origin for HTTP, so the HttpOnly auth cookie is first-party.
- WebSockets (recognition and chat) connect to the backend directly at
  `ws(s)://<page hostname>:NEXT_PUBLIC_BACKEND_PORT`, or at
  `NEXT_PUBLIC_WS_URL` if set. They authenticate with a short-lived ticket
  from `api.getWsUrl()`.
- `src/middleware.ts` redirects signed-out visitors to `/auth?next=...`
  for every page except `/` and `/auth`.
- All API calls go through `src/app/utils/api.ts`.

## Pages

| Route | Purpose |
| ----- | ------- |
| `/` | Landing page |
| `/auth` | Sign in / register |
| `/dashboard` | XP, streak, activity, recommendations |
| `/translate` | Live webcam recognition with AR overlay and voice output |
| `/text`, `/voice` | Text or speech → ISL signs (English and Hindi) |
| `/learning` | Dictionary, camera practice, proficiency matrix, quiz |
| `/dictionary` | Full ISL dictionary |
| `/game` | Timed sign challenge |
| `/community`, `/chat` | Feed, comments, likes; direct messages |
| `/profile` | Account details, level, achievements |

## Scripts

```bash
npm run dev      # development server on :3000
npm run lint     # ESLint (also enforced during build)
npm run build    # production build (standalone output for Docker)
npm start
```
