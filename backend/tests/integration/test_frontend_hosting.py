from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_serves_single_container_frontend(monkeypatch, tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<main>DataTrust Workbench</main>")
    (tmp_path / "assets" / "app.js").write_text("console.log('ready')")
    monkeypatch.setenv("DATATRUST_STATIC_DIR", str(tmp_path))
    get_settings.cache_clear()

    try:
        with TestClient(create_app()) as client:
            assert client.get("/").text == "<main>DataTrust Workbench</main>"
            assert client.get("/rules").text == "<main>DataTrust Workbench</main>"
            assert client.get("/assets/app.js").text == "console.log('ready')"
            assert client.get("/api/v1/not-a-route").status_code == 404
    finally:
        get_settings.cache_clear()
