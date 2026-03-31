# example_app

Example Mountaineer app that integrates `mountaineer-auth` end to end.

The app includes:

- a concrete `User` model backed by the auth mixin
- packaged login, signup, and logout flows
- an unauthorized redirect that preserves the protected destination
- a homepage that drives into a protected detail page
- a seeded detail record so the POC works on first boot

## Getting Started

Start the local Docker stack:

```bash
docker compose up --build
```

Then open `http://localhost:3000/`.

The web app bootstraps its schema on first startup, seeds a default detail
record, and lets you sign up before visiting the protected page.

Waymark also starts as part of the local stack. Its dashboard is available at
`http://127.0.0.1:5008/`.

Email previews are available in the admin console at
`http://localhost:3000/admin/email/`, including the auth emails and the example
welcome preview.

By default the example app includes dummy Resend and auth-email settings, but
auth email delivery is disabled so the app can boot without real credentials.

## Real Email Delivery

To enable actual auth email sending through Resend, run Docker Compose with
real credentials and sender metadata overrides:

```bash
AUTH_EMAIL_ENABLED=true \
RESEND_API_KEY=re_xxxxxxxxxxxxx \
AUTH_EMAIL__FROM_EMAIL=onboarding@resend.dev \
docker compose up --build
```

The default `AUTH_EMAIL__SERVER_HOST` is already `http://localhost:3000`, so
the verification and reset links work locally unless you want to override it.

## Local Development

```bash
uv run createdb
uv run runserver --host 0.0.0.0 --port 3000
```
