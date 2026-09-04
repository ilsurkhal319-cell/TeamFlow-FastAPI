# TeamFlow React

Production web client for TeamFlow built with Vite, React and TypeScript. It talks to FastAPI through the same-origin `/api/v1` proxy and uses the `/ws/` channel for board events.

```bash
npm install
npm run dev
```

The production image builds the static bundle and serves it with Nginx. Docker Compose exposes it at `http://localhost:5173`.
