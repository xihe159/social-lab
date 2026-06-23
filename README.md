# Social Lab

Social Lab is an AI-powered communication simulation product for rehearsing difficult conversations before they happen.

The current repository is a Next.js Web MVP. It preserves the original static prototype experience while providing a maintainable structure for adding real AI services, APIs, persistence, and authentication.

## Current Features

- Responsive desktop and mobile experience
- Advisor, workplace, and social communication scenarios
- Communication goal and target-person forms
- Persona Card and Relationship State generation
- Rule-based multi-turn simulation
- Outcome prediction and communication coaching report
- Copy-ready rewrite and retry flow

The current simulation logic is still local and deterministic. No user data is sent to an external AI provider.

## Tech Stack

- Next.js App Router
- React
- TypeScript
- Lucide React icons
- CSS

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
│   ├── social-lab-data.ts
│   ├── social-lab-logic.ts
│   └── social-lab-types.ts
├── docs/
├── reference-media/
├── package.json
├── tsconfig.json
└── next.config.ts
```

## Local Development

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

Create a production build:

```bash
npm run build
```

## Architecture Notes

- `app/` owns routing, metadata, and global styles.
- `components/social-lab/` owns the interactive product UI.
- `components/social-lab/screens/` contains the six user-flow screens.
- `lib/social-lab-data.ts` contains scenario presets and UI labels.
- `lib/social-lab-logic.ts` contains the temporary local simulation rules.
- `lib/social-lab-types.ts` contains shared domain types.

The local logic layer is intentionally separated so it can later be replaced by server-side API calls without rebuilding the interface.

## Recommended Next Milestones

1. Add `POST /api/persona/create` with structured LLM output.
2. Add `POST /api/session/message` for real target-person simulation.
3. Add Supabase persistence for personas, sessions, messages, states, and reports.
4. Add session memory and Relationship State updates.
5. Add real Prediction and Coach services.
6. Add anonymous sessions, authentication, analytics, and privacy controls.
7. Deploy to Vercel and test with real users.

## Product Note

Social Lab is a communication rehearsal and decision-support tool. It does not automatically contact real people or guarantee real-world outcomes.
