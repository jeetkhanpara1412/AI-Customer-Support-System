# Repository guidance

- Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL, Redis.
- Frontend: React + TypeScript + Vite, Tailwind CSS, React Router, Axios, TanStack Query, Zustand, React Hook Form, and Zod.
- Keep JWT access tokens in memory only. Refresh tokens belong only in the scoped, HttpOnly cookie.
- Never put credentials or access tokens in WebSocket URLs. Authenticate the socket with its first message.
- Validate all client input and enforce ownership/administrator checks in backend routes.
- Do not log passwords, tokens, or sensitive customer message bodies.
- Security/Fraud classification always escalates to a human agent.
- Prefer SQLAlchemy ORM expressions, explicit CORS origins, safe JSON errors, and plain-text message rendering.
- Pin dependencies and run `ruff check .` plus `pytest -q` from `backend/`; run `npm run lint`, `npm test`, and `npm run build` from `frontend/`.
