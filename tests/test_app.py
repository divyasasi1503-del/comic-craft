from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json()["status"] == "ok"


def test_homepage():

    response = client.get("/")

    assert response.status_code == 200

    assert "COMICCRAFT" in response.text


def test_test_image():

    response = client.post(
        "/test-image",
        data={
            "prompt":
            "A friendly fox in a forest"
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["image_path"]
        .startswith(
            "/static/panels/"
        )
    )