import asyncpg
import pytest
import pytest_asyncio
from iceaxe import DBConnection
from iceaxe.mountaineer import DatabaseConfig
from iceaxe.schemas.cli import create_all
from mountaineer_email.registry import clear_email_registry as _clear_email_registry

from mountaineer_auth.__tests__ import conf_models as models
from mountaineer_auth.config import AuthRecaptchaConfig


@pytest.fixture(autouse=True)
def clear_registries():
    """
    Allow us to re-register controllers with the same name when
    running in the same testing session.

    """
    _clear_email_registry()


@pytest.fixture(autouse=True)
def config() -> models.AppConfig:
    common_db = DatabaseConfig(
        POSTGRES_HOST="localhost",
        POSTGRES_USER="mountaineer_auth",
        POSTGRES_PASSWORD="mysecretpassword",
        POSTGRES_DB="mountaineer_auth_test_db",
        POSTGRES_PORT=5436,
    )

    return models.AppConfig(
        **common_db.model_dump(),
        API_SECRET_KEY="test-api-secret",
        RECAPTCHA_ENABLED=True,
        RECAPTCHA=AuthRecaptchaConfig(
            gcp_service="test-service",
            gcp_project_id="test-project-id",
            gcp_client_key="test-client-key",
        ),
        AUTH_USER=models.User,
        AUTH_VERIFICATION_STATE=models.VerificationState,
    )


@pytest_asyncio.fixture
async def db_connection(config: models.AppConfig):
    db_connection = DBConnection(
        await asyncpg.connect(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            database=config.POSTGRES_DB,
        )
    )

    # Step 1: Drop all tables in the public schema
    await db_connection.conn.execute(
        """
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END $$;
    """
    )

    # Step 2: Drop all custom types in the public schema
    await db_connection.conn.execute(
        """
        DO $$ DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT typname FROM pg_type WHERE typtype = 'e' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')) LOOP
                EXECUTE 'DROP TYPE IF EXISTS ' || quote_ident(r.typname) || ' CASCADE';
            END LOOP;
        END $$;
    """
    )

    await create_all(db_connection)

    return db_connection
