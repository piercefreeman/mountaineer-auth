from fastapi.testclient import TestClient

from mountaineer_auth.plugin import create_plugin


def test_plugin_boots_with_mountaineer() -> None:
    component = create_plugin().to_webserver()

    with TestClient(component.app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/auth/login" in response.json()["paths"]
