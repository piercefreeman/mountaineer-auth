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

## Local Development

```bash
uv run createdb
uv run runserver --host 0.0.0.0 --port 3000
```
