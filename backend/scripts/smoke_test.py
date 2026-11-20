import asyncio
import json
import os
from uuid import uuid4

import httpx
import websockets

BASE_URL = os.getenv("SMOKE_BASE_URL", "http://127.0.0.1:8000")
WS_URL = BASE_URL.replace("https://", "wss://").replace("http://", "ws://") + "/ws/chat"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


async def main() -> None:
    admin_email = os.environ.get("ADMIN_EMAIL", "")
    admin_password = os.environ.get("ADMIN_PASSWORD", "")
    require(
        bool(admin_email and admin_password),
        "ADMIN_EMAIL and ADMIN_PASSWORD must be set",
    )
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
        email = f"smoke-{uuid4().hex}@example.com"
        registration = await client.post(
            "/api/auth/register",
            json={
                "name": "Smoke Test User",
                "email": email,
                "password": "StrongPassword123",
            },
        )
        require(
            registration.status_code == 201,
            f"Registration failed: {registration.status_code}",
        )
        user_login = await client.post(
            "/api/auth/login",
            json={"email": email, "password": "StrongPassword123"},
        )
        require(user_login.status_code == 200, "User login failed")
        user_token = user_login.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        user_me = await client.get("/api/auth/me", headers=user_headers)
        require(
            user_me.status_code == 200 and user_me.json()["role"] == "user",
            "Customer session role was not returned",
        )
        forbidden_stats = await client.get(
            "/api/admin/stats", headers=user_headers
        )
        require(forbidden_stats.status_code == 403, "Customer accessed admin stats")

        regular_chat = await client.post(
            "/api/chat",
            headers=user_headers,
            json={"message": "Where can I find general support information?"},
        )
        require(regular_chat.status_code == 200, "Regular chat failed")

        async with websockets.connect(WS_URL) as socket:
            await socket.send(json.dumps({"type": "auth", "access_token": user_token}))
            await socket.send(
                json.dumps(
                    {
                        "type": "user_message",
                        "text": "I do not recognize this unauthorized transaction",
                    }
                )
            )
            typing_event = json.loads(await socket.recv())
            require(
                typing_event.get("type") == "typing", "WebSocket typing event missing"
            )
            fraud_event = await socket.recv()
            fraud_result = json.loads(fraud_event)
            require(
                fraud_result["type"] == "assistant_message",
                "WebSocket assistant reply missing",
            )
            require(
                fraud_result["escalated"] is True, "Fraud message was not escalated"
            )
            ticket_id = fraud_result["ticket_id"]

            tickets = await client.get("/api/tickets", headers=user_headers)
            require(
                tickets.status_code == 200
                and any(item["id"] == ticket_id for item in tickets.json()),
                "Escalated ticket missing",
            )
            ticket_detail = await client.get(
                f"/api/tickets/{ticket_id}", headers=user_headers
            )
            require(ticket_detail.status_code == 200, "Ticket detail unavailable")

            admin_login = await client.post(
                "/api/auth/login",
                json={"email": admin_email, "password": admin_password},
            )
            require(admin_login.status_code == 200, "Admin login failed")
            admin_headers = {
                "Authorization": f"Bearer {admin_login.json()['access_token']}"
            }
            admin_me = await client.get("/api/auth/me", headers=admin_headers)
            require(
                admin_me.status_code == 200 and admin_me.json()["role"] == "admin",
                "Seeded administrator role was not returned",
            )
            ticket_list = await client.get(
                "/api/admin/tickets?priority=high&page=1", headers=admin_headers
            )
            require(
                ticket_list.status_code == 200
                and any(item["id"] == ticket_id for item in ticket_list.json()),
                "Admin ticket listing failed",
            )
            updated = await client.patch(
                f"/api/admin/tickets/{ticket_id}",
                headers=admin_headers,
                json={"status": "in_progress"},
            )
            require(
                updated.status_code == 200
                and updated.json()["status"] == "in_progress",
                "Ticket status update failed",
            )
            reply = await client.post(
                f"/api/admin/tickets/{ticket_id}/reply",
                headers=admin_headers,
                json={
                    "text": "A support specialist is reviewing this security concern."
                },
            )
            require(reply.status_code == 200, "Admin ticket reply failed")
            agent_event = json.loads(await socket.recv())
            require(
                agent_event["type"] == "agent_message",
                "Live admin reply was not delivered",
            )

            stats = await client.get("/api/admin/stats", headers=admin_headers)
            require(
                stats.status_code == 200 and "open_tickets" in stats.json(),
                "Admin stats unavailable",
            )
            knowledge = await client.get(
                "/api/admin/knowledge", headers=admin_headers
            )
            require(knowledge.status_code == 200, "Admin knowledge base unavailable")
            knowledge_entry = await client.post(
                "/api/admin/knowledge",
                headers=admin_headers,
                json={
                    "message": "Smoke test knowledge example",
                    "category": "General Inquiry",
                    "response": "This temporary example is used by the smoke test.",
                },
            )
            require(knowledge_entry.status_code == 201, "Knowledge add failed")
            knowledge_id = knowledge_entry.json()["id"]
            knowledge_update = await client.put(
                f"/api/admin/knowledge/{knowledge_id}",
                headers=admin_headers,
                json={
                    "message": "Updated smoke test example",
                    "category": "General Inquiry",
                    "response": "This temporary example was updated.",
                },
            )
            require(knowledge_update.status_code == 200, "Knowledge update failed")
            knowledge_delete = await client.delete(
                f"/api/admin/knowledge/{knowledge_id}", headers=admin_headers
            )
            require(knowledge_delete.status_code == 204, "Knowledge delete failed")
            users = await client.get("/api/admin/users", headers=admin_headers)
            require(
                users.status_code == 200
                and any(item["email"] == email for item in users.json()),
                "Admin user listing failed",
            )
            retrained = await client.post("/api/admin/retrain", headers=admin_headers)
            require(
                retrained.status_code == 200 and retrained.json()["samples"] > 0,
                "Model retraining failed",
            )
            logout = await client.post("/api/auth/logout", headers=admin_headers)
            require(logout.status_code == 204, "Admin logout failed")
            logout = await client.post("/api/auth/logout", headers=user_headers)
            require(logout.status_code == 204, "User logout failed")
    print(
        "Smoke test passed: register, login, chat, fraud escalation, ticket, admin flow, retrain, live reply, logout."
    )


if __name__ == "__main__":
    asyncio.run(main())
