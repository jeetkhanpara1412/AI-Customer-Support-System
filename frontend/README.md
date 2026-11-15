# Frontend

React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Zustand, and React Hook Form provide the customer and admin interfaces.

## Development

```bash
npm ci
cp .env.example .env
npm run dev
```

The Vite server runs at `http://localhost:5173`. Configure `VITE_API_URL` to the backend API base URL (default `/api`) when needed. `VITE_WS_URL` can override the WebSocket endpoint; if it is empty, the app uses the current host and `/ws/chat`.

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `VITE_API_URL` | `/api` | HTTP API base URL |
| `VITE_WS_URL` | empty | Optional WebSocket URL; empty uses the current host |
| `VITE_USE_MOCK` | `false` | Start the MSW worker for local mock responses when set to `true` |

MSW is development-only; production builds use the real API. Its worker asset is generated under `public/`.

## Checks

```bash
npm run lint
npm test
npm run build
```

Tests use Vitest, Testing Library, and MSW. The API client validates key responses with Zod, stores access tokens in memory, and uses the HttpOnly refresh cookie when an API request needs renewal.
