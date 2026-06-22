# Social Lab

Social Lab is an AI-powered communication simulation concept for rehearsing difficult conversations before they happen.

This repository currently contains a static Web MVP prototype. It demonstrates the core product flow from scenario selection to persona creation, simulated conversation, and communication coaching report.

## Current Version

The current build is a front-end prototype:

- Landing page and product positioning
- Scenario selection for advisor, workplace, and social communication
- Target-person input form
- Persona Card and Relationship State display
- Rule-based simulated chat experience
- Outcome prediction and communication coaching report
- Responsive layout for desktop and mobile

This version does not yet include real AI calls, a backend API, database persistence, login, or long-term memory.

## Project Structure

```text
social-lab/
├── index.html
├── app.js
├── styles.css
├── README.md
├── .gitignore
├── reference-media/
│   ├── prototype-01.png
│   ├── prototype-02.png
│   └── ...
└── docs/
    ├── PRD.md
    └── SYSTEM_DESIGN.md
```

## How to Run

Open `index.html` directly in a browser.

For a local preview server:

```bash
python -m http.server 8000
```

Then open:

```text
http://127.0.0.1:8000/index.html
```

## Roadmap

1. Convert the static prototype into a Next.js application.
2. Add `/api/persona/create` to generate Persona Card and Relationship State with an LLM.
3. Add `/api/session/create` and `/api/session/message` for real simulated conversations.
4. Add a database such as Supabase for personas, sessions, messages, states, and reports.
5. Add session memory and state updates.
6. Add report generation with prediction and communication coaching.
7. Add deployment, analytics, privacy handling, and error states.

## Product Note

Social Lab is not designed to automatically contact real people or guarantee real-world outcomes. It is a communication rehearsal and decision-support tool.
