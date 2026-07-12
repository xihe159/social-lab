# Social Lab

Social Lab is an AI-powered communication rehearsal product. It helps users practice difficult conversations with an AI-simulated target person before speaking in real life.

Online demo:

https://xihe159.github.io/social-lab/

> The web app is hosted on GitHub Pages. Real AI features require the FastAPI backend to be deployed separately and configured through `NEXT_PUBLIC_AGENT_API_BASE_URL`.
> Current backend: https://social-lab-backend.onrender.com

## Current Features

- Responsive desktop and mobile web experience
- Supabase Email Magic Link login with optional anonymous trial
- Saved personas, sessions, messages, and reports for logged-in users
- History, persona library, and profile pages
- Advisor, workplace, and social communication scenarios
- Goal, expected outcome, target-person profile, relationship, habit, and chat-log input
- AI-generated Persona Card and Relationship State
- AI target-person replies through the backend session API
- AI communication report with success probability, risks, improvement factors, and rewrite suggestion
- Copy-ready rewrite and retry flow

## Architecture

```text
GitHub Pages static frontend
        |
        | NEXT_PUBLIC_AGENT_API_BASE_URL / Supabase Auth
        v
Render FastAPI backend
        |
        | LLM provider + Supabase PostgreSQL
```

The frontend is a static Next.js export. GitHub Pages cannot run server code, so the Python backend must be deployed on Render or another web service.

## Project Structure

```text
social-lab/
├── app/
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   └── social-lab/
│       ├── screens/
│       ├── mobile-header.tsx
│       ├── sidebar.tsx
│       └── social-lab-app.tsx
├── lib/
│   ├── social-lab-api.ts
│   ├── social-lab-data.ts
│   ├── social-lab-logic.ts
│   └── social-lab-types.ts
├── backend/
│   ├── app/
│   └── requirements.txt
├── .github/
│   └── workflows/
│       └── deploy-pages.yml
├── docs/
├── reference-media/
├── package.json
├── tsconfig.json
└── next.config.ts
```

## Local Development

Install frontend dependencies:

```bash
npm install
```

Create `.env.local` in the project root:

```env
NEXT_PUBLIC_AGENT_API_BASE_URL=https://social-lab-backend.onrender.com
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

If you are running the backend locally, use `http://127.0.0.1:8000` instead.

Start the frontend:

```bash
npm run dev
```

Because the project is configured for GitHub Pages, open:

```text
http://localhost:3000/social-lab/
```

Run checks:

```bash
npm run lint
npm run build
```

## Backend Development

Install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://your-openai-compatible-base-url
LLM_MODEL_ID=your_model_id
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
```

Before enabling V1.5 persistence, run `backend/supabase_schema.sql` in the
Supabase SQL editor. In Supabase Auth settings, add these redirect URLs:

```text
http://localhost:3000/social-lab/auth/callback/
https://xihe159.github.io/social-lab/auth/callback/
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

Health check:

```text
http://127.0.0.1:8000/health
```

Main backend APIs:

- `POST /api/persona/create`
- `POST /api/session/message`
- `POST /api/session/report`
- `GET /api/me`
- `GET /api/personas`
- `GET /api/sessions`
- `GET /health`

## Deploy Frontend To GitHub Pages

This repository includes `.github/workflows/deploy-pages.yml`.

Before deploying, add this GitHub repository variable:

```text
NEXT_PUBLIC_AGENT_API_BASE_URL=https://social-lab-backend.onrender.com
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Then enable GitHub Pages:

1. Open repository Settings.
2. Go to Pages.
3. Choose GitHub Actions as the source.
4. Push to `main`.

The site will be published to:

```text
https://xihe159.github.io/social-lab/
```

## Deploy Backend To Render

Create a new Render Web Service with:

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Add Render environment variables:

```text
LLM_API_KEY
LLM_BASE_URL
LLM_MODEL_ID
SUPABASE_URL
SUPABASE_SERVICE_KEY
```

After deployment, copy the Render service URL and set it as the GitHub repository variable `NEXT_PUBLIC_AGENT_API_BASE_URL`.

Backend API docs:

```text
https://social-lab-backend.onrender.com/docs
```

Supabase backend connection check:

```text
https://social-lab-backend.onrender.com/api/debug/supabase
```

## Privacy Note

Social Lab sends user-provided communication goals, relationship descriptions, chat drafts, and conversation messages to the deployed backend and configured model provider for simulation. Do not enter ID numbers, phone numbers, addresses, bank card details, passwords, or other sensitive personal information.

Social Lab is a rehearsal and decision-support tool. It does not contact real people and cannot guarantee real-world outcomes.
