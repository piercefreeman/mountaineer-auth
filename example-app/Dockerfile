# Local development Dockerfile for running the example app with hot-reload.
#
# The compose file builds from the repo root so we can install the local
# `mountaineer_auth` package and mount both codebases into the container.

FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3.12 \
        python3.12-venv \
        python3.12-dev \
        gcc \
        curl \
        ca-certificates \
        gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
        | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /usr/src/app/example-app

COPY pyproject.toml /usr/src/app/pyproject.toml
COPY README.md /usr/src/app/README.md
COPY mountaineer_auth /usr/src/app/mountaineer_auth

COPY example-app/pyproject.toml example-app/uv.lock example-app/README.md ./
COPY example-app/example_app/views/package.json example-app/example_app/views/package-lock.json ./example_app/views/

RUN uv venv --python python3.12
ENV VIRTUAL_ENV=/usr/src/app/example-app/.venv
ENV PATH="/usr/src/app/example-app/.venv/bin:$PATH"
# The build step imports the app controller, which validates the database config.
# Compose overrides these at runtime, but we need stable defaults inside the image.
ENV POSTGRES_HOST=postgres \
    POSTGRES_PORT=5432 \
    POSTGRES_USER=example_app \
    POSTGRES_PASSWORD=mysecretpassword \
    POSTGRES_DB=example_app_db \
    ENVIRONMENT=development

RUN uv sync --frozen --no-install-project
RUN npm install --prefix /usr/src/app/example-app/example_app/views

COPY example-app/example_app ./example_app

RUN uv sync --frozen
RUN uv run --no-sync build

EXPOSE 3000

CMD ["uv", "run", "runserver", "--host", "0.0.0.0", "--port", "3000"]
