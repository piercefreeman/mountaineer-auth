import subprocess

from fastapi.testclient import TestClient

from mountaineer.cli import handle_build

from mountaineer_auth.plugin import create_plugin
from mountaineer_auth.views import get_auth_view_path


def test_plugin_boots_with_mountaineer() -> None:
    component = create_plugin().to_webserver()

    with TestClient(component.app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/auth/login" in response.json()["paths"]


def test_plugin_frontend_builds() -> None:
    view_root = get_auth_view_path("")
    subprocess.run(["npm", "ci"], cwd=view_root, check=True)

    handle_build(webcontroller="mountaineer_auth.cli:app")

    for relative_path in (
        ".mountaineer/static/auth_main.css",
        ".mountaineer/static/login_controller.js",
        ".mountaineer/ssr/login_controller.js",
    ):
        output = view_root / relative_path
        assert output.is_file() and output.stat().st_size > 0
