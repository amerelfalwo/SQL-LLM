# web — Next.js frontend

Text-to-SQL playground UI (App Router, TypeScript, vanilla CSS). It proxies `/api/v1/*` to the FastAPI
backend (`BACKEND_URL`, default `http://127.0.0.1:8000`), so start the backend first.
See the [root README](../README.md) for full setup.

```bash
npm install
npm run dev     # http://localhost:3000
npm run lint
```

- `src/app/` — page, layout, global styles
- `src/components/` — `SchemaSidebar`, `ResultTable`
- `src/lib/api.ts` — typed API client
