# CloudBase Setup

Social Lab V1.5 uses CloudBase Auth and CloudBase Database on the frontend.
The FastAPI backend only runs AI agent APIs.

## Frontend Environment Variable

Set this GitHub Actions repository variable:

```text
NEXT_PUBLIC_CLOUDBASE_ENV_ID=social-lab-d4g9g9ab34e44d7cb
NEXT_PUBLIC_CLOUDBASE_REGION=ap-shanghai
NEXT_PUBLIC_CLOUDBASE_PUBLISHABLE_KEY=your-cloudbase-publishable-key
```

For local development, add it to `.env.local`.

`NEXT_PUBLIC_CLOUDBASE_PUBLISHABLE_KEY` is safe for browser builds. Do not put
the CloudBase Server API Key in GitHub Pages, `.env.local` for frontend code, or
any `NEXT_PUBLIC_` variable.

## Auth Providers

Enable these CloudBase authentication providers:

- Email verification code
- Username and password

## Database Collections

Create these collections:

```text
personas
sessions
messages
reports
relationship_states
```

All records written by Social Lab include an `owner_id` field. Configure
database permissions so users can only read and write their own records.

Suggested rule shape:

```js
{
  "read": "auth != null && doc.owner_id == auth.uid",
  "write": "auth != null && doc.owner_id == auth.uid"
}
```

For `messages`, `reports`, and `relationship_states`, records are linked by
`session_id`. If collection-level linked rules are hard to express in your
CloudBase plan, start with authenticated-user-only permissions during testing,
then move these writes behind a CloudBase Function in the next hardening pass.
