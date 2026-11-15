from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core.rate_limit import limiter
from app.db.models import User
from app.db.session import SessionLocal
from app.main import create_app


@pytest.fixture
def client():
    limiter.reset()
    with TestClient(create_app()) as test_client:
        yield test_client
    limiter.reset()


def register_and_login(client: TestClient, role: str = "user") -> tuple[dict, str]:
    email = f"{uuid4().hex}@example.com"
    response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "StrongPassword123"},
    )
    assert response.status_code == 201
    if role == "admin":
        with SessionLocal() as db:
            user = db.query(User).filter_by(email=email).one()
            user.role = "admin"
            db.commit()
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "StrongPassword123"},
    )
    assert login.status_code == 200
    return login.json()["user"], login.json()["access_token"]


def test_health_checks_database_and_redis(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["db"] is True
    assert "redis" in response.json()
    assert response.headers["content-security-policy"]


def test_register_login_and_csrf_protected_refresh(client: TestClient):
    user, _ = register_and_login(client)
    assert set(user) == {"id", "name", "email", "role"}
    assert "refresh_token" in client.cookies
    assert client.post("/api/auth/refresh").status_code == 403
    refreshed = client.post("/api/auth/refresh", headers={"X-Requested-With": "fetch"})
    assert refreshed.status_code == 200
    assert "access_token" in refreshed.json()


def test_validation_error_uses_contract_shape(client: TestClient):
    response = client.post("/api/auth/register", json={"name": "", "email": "invalid", "password": "short"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unexpected_error_uses_safe_contract_shape(monkeypatch: pytest.MonkeyPatch):
    with TestClient(create_app(), raise_server_exceptions=False) as test_client:
        _, token = register_and_login(test_client)

        def fail_chat(*_args, **_kwargs):
            raise RuntimeError("private detail")

        monkeypatch.setattr(
            "app.api.routes.chat.process_chat",
            fail_chat,
        )
        response = test_client.post(
            "/api/chat",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": "I need help"},
        )
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "An unexpected error occurred"}
    }


def test_fraud_chat_creates_high_priority_ticket(client: TestClient):
    _, token = register_and_login(client)
    response = client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "I do not recognize this unauthorized transaction"},
    )
    assert response.status_code == 200
    assert response.json()["category"] == "Security / Fraud"
    assert response.json()["mode"] == "fallback"
    assert response.json()["escalated"] is True
    tickets = client.get("/api/tickets", headers={"Authorization": f"Bearer {token}"})
    assert tickets.json()[0]["priority"] == "high"


def test_user_cannot_read_other_conversations_or_admin_routes(client: TestClient):
    _, first_token = register_and_login(client)
    _, other_token = register_and_login(client)
    chat = client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {first_token}"},
        json={"message": "How can I contact support?"},
    ).json()
    headers = {"Authorization": f"Bearer {other_token}"}
    assert client.get(f"/api/conversations/{chat['conversation_id']}", headers=headers).status_code == 404
    assert client.get("/api/admin/stats", headers=headers).status_code == 403


def test_admin_can_manage_ticket_reply_status_and_stats(client: TestClient):
    _, owner_token = register_and_login(client)
    _, admin_token = register_and_login(client, role="admin")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    chat = client.post(
        "/api/chat",
        headers=owner_headers,
        json={"message": "I see a suspicious charge I do not recognize"},
    ).json()
    ticket_id = chat["ticket_id"]

    listed = client.get("/api/admin/tickets?priority=high&page=1", headers=admin_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["subject"]
    updated = client.patch(
        f"/api/admin/tickets/{ticket_id}",
        headers=admin_headers,
        json={"status": "in_progress"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "in_progress"
    reply = client.post(
        f"/api/admin/tickets/{ticket_id}/reply",
        headers=admin_headers,
        json={"text": "A support specialist is reviewing this report."},
    )
    assert reply.status_code == 200
    user_ticket = client.get(f"/api/tickets/{ticket_id}", headers=owner_headers)
    assert user_ticket.json()["replies"][0]["text"] == "A support specialist is reviewing this report."
    stats = client.get("/api/admin/stats", headers=admin_headers)
    assert stats.status_code == 200
    assert set(stats.json()) == {"open_tickets", "resolved_today", "escalation_rate", "avg_confidence", "by_category"}


def test_logout_revokes_refresh_token(client: TestClient):
    _, token = register_and_login(client)
    assert client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"}).status_code == 204
    assert client.post("/api/auth/refresh", headers={"X-Requested-With": "fetch"}).status_code == 401


def test_websocket_rejects_missing_auth(client: TestClient):
    with pytest.raises(WebSocketDisconnect) as error:
        with client.websocket_connect("/ws/chat") as websocket:
            websocket.send_json({"type": "auth", "access_token": "invalid"})
            websocket.receive_json()
    assert error.value.code == 4401


def test_login_is_rate_limited_per_email(client: TestClient):
    email = f"{uuid4().hex}@example.com"
    for _ in range(5):
        response = client.post("/api/auth/login", json={"email": email, "password": "WrongPassword123"})
        assert response.status_code == 401
    response = client.post("/api/auth/login", json={"email": email, "password": "WrongPassword123"})
    assert response.status_code == 429
