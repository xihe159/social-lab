# Social Lab V1 System Design Summary

## Current Implementation

The current repository is a Next.js App Router application:

- `app/` contains routing, metadata, and global styles.
- `components/social-lab/` contains the application shell and flow screens.
- `lib/social-lab-data.ts` contains scenario presets.
- `lib/social-lab-logic.ts` contains temporary local simulation rules.
- `lib/social-lab-types.ts` contains shared TypeScript domain types.

No real backend, database, or LLM integration is included yet. The local rule layer is separated so it can be replaced by API calls incrementally.

## Target V1 Architecture

```text
Frontend
  ↓
API Routes
  ↓
Persona Service
State Service
Memory Service
Simulation Service
Prediction Service
Coach Service
  ↓
Database
  ↓
LLM Provider
```

## Recommended API Endpoints

### `POST /api/persona/create`

Creates a target-person Persona Card and initial Relationship State.

### `PATCH /api/persona/update`

Allows the user to correct or refine the generated persona.

### `POST /api/session/create`

Creates a simulation session.

### `POST /api/session/message`

Sends a user message and returns the simulated target-person reply.

### `POST /api/session/report`

Generates outcome prediction and communication coaching.

### `GET /api/session/:id`

Returns a saved simulation session, including messages, state, memory, persona, and report.

## Recommended Database Tables

- `personas`
- `relationship_states`
- `simulation_sessions`
- `messages`
- `memory_summaries`
- `reports`
- `events`

## Service Responsibilities

### Persona Service

Generates structured information about the simulated target person, including communication style, response speed, decision style, sensitivities, risk points, and recommended strategy.

### State Service

Generates and updates Relationship State:

- trust
- respect
- familiarity
- affinity
- authority distance
- emotional debt

### Memory Service

Maintains lightweight session memory:

- conversation summary
- user behavior tags
- target focus tags
- important events

### Simulation Service

Generates the target person's next reply based on persona, relationship state, memory, recent messages, and the user's communication goal.

### Prediction Service

Generates success rate and possible outcome distribution:

- accept
- hesitate
- reject
- ignore

### Coach Service

Analyzes the user's expression and returns strengths, problems, suggestions, a copy-ready rewrite, and next-step advice.

## Recommended Build Steps

1. Keep the current Next.js interface as the UX baseline.
2. Add backend API routes.
3. Add LLM prompts and JSON schema validation.
4. Add Supabase or another database.
5. Add memory and state update loops.
6. Replace local report rules with Prediction and Coach services.
7. Add authentication, privacy controls, and analytics.
8. Deploy to Vercel and test with real users.
