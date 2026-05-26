# Book Condenser Frontend

Standalone React frontend for the Book Condenser FastAPI backend.

## Local Setup

```bash
npm install
cp .env.example .env
npm run dev
```

For local development, `VITE_API_BASE_URL=/api` uses the Vite proxy and avoids browser CORS issues. The proxy forwards `/api` to `http://127.0.0.1:8000`.

For deployment, set `VITE_API_BASE_URL` to your hosted backend URL, or add an equivalent `/api` rewrite in your frontend host.

## API Contract

- `POST /auth/signup` accepts `{ "email", "password", "full_name" }`.
- `POST /auth/login` accepts form fields `username` and `password`.
- `GET /auth/me` requires `Authorization: Bearer <token>`.
- `POST /auth/upload` requires `Authorization: Bearer <token>` and multipart field `file`.

The UI allows one active upload at a time and shows the returned download link when processing completes.
