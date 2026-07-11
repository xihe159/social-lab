# CloudBase Backend Setup

Social Lab now uses CloudBase only from the Render FastAPI backend. The browser
does not call CloudBase Auth or CloudBase Database directly.

## Render Environment Variables

Add these variables to the Render backend service:

```text
CLOUDBASE_ENV_ID=social-lab-d4g9g9ab34e44d7cb
CLOUDBASE_REGION=ap-shanghai
CLOUDBASE_SERVER_API_KEY=your-cloudbase-server-api-key
```

Do not add `CLOUDBASE_SERVER_API_KEY` to GitHub Pages, frontend `.env.local`, or
any `NEXT_PUBLIC_` variable.

## Database Collections

Create these CloudBase collections:

```text
personas
sessions
messages
reports
relationship_states
```

New Social Lab records use `anonymous_id` as the user identity. The value comes
from the frontend-generated `sl_anon_<uuid>` stored in browser `localStorage`.

Recommended database posture:

- Disable direct browser writes.
- Let only the backend Server API Key write data.
- Keep records queryable by `anonymous_id` for history, persona library, and
  report lookup.

## Notes

CloudBase Auth providers are no longer required for V1.5 anonymous usage.
Existing old `owner_id` records are not migrated by this version.
