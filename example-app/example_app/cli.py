from click import command, group, option
from iceaxe import DBConnection
from iceaxe.migrations.cli import handle_apply, handle_generate, handle_rollback
from iceaxe.mountaineer import DatabaseDependencies

from mountaineer import CoreDependencies, Depends
from mountaineer.cli import handle_build, handle_runserver, handle_watch
from mountaineer.dependencies import get_function_dependencies
from mountaineer.io import async_to_sync

from example_app.bootstrap import bootstrap_database
from example_app.config import AppConfig
from example_app.postcss_compat import ensure_postcss_bin


@command()
@option("--host", default="127.0.0.1", help="Host to bind the server to")
@option("--port", default=5006, help="Port to run the server on")
def runserver(host: str, port: int):
    ensure_postcss_bin()
    handle_runserver(
        package="example_app",
        webservice="example_app.main:app",
        webcontroller="example_app.app:controller",
        host=host,
        port=port,
    )


@command()
def watch():
    ensure_postcss_bin()
    handle_watch(
        package="example_app",
        webcontroller="example_app.app:controller",
    )


@command()
def build():
    ensure_postcss_bin()
    handle_build(
        webcontroller="example_app.app:controller",
    )


@command()
@async_to_sync
async def createdb():
    _ = AppConfig()  # type: ignore

    async def run_bootstrap(
        db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
    ):
        await bootstrap_database(db_connection)

    async with get_function_dependencies(callable=run_bootstrap) as values:
        await run_bootstrap(**values)


@group
def migrate():
    pass


@migrate.command()
@option("--message", required=False)
@async_to_sync
async def generate(message: str | None):
    async def _inner(
        config: AppConfig = Depends(CoreDependencies.get_config_with_type(AppConfig)),
        db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
    ):
        assert config.PACKAGE
        await handle_generate(config.PACKAGE, db_connection, message=message)

    _ = AppConfig()  # type: ignore
    async with get_function_dependencies(callable=_inner) as deps:
        await _inner(**deps)


@migrate.command()
@async_to_sync
async def apply():
    async def _inner(
        config: AppConfig = Depends(CoreDependencies.get_config_with_type(AppConfig)),
        db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
    ):
        assert config.PACKAGE
        await handle_apply(config.PACKAGE, db_connection)

    _ = AppConfig()  # type: ignore
    async with get_function_dependencies(callable=_inner) as deps:
        await _inner(**deps)


@migrate.command()
@async_to_sync
async def rollback():
    async def _inner(
        config: AppConfig = Depends(CoreDependencies.get_config_with_type(AppConfig)),
        db_connection: DBConnection = Depends(DatabaseDependencies.get_db_connection),
    ):
        assert config.PACKAGE
        await handle_rollback(config.PACKAGE, db_connection)

    _ = AppConfig()  # type: ignore
    async with get_function_dependencies(callable=_inner) as deps:
        await _inner(**deps)
