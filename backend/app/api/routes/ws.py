import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import get_settings
from app.core.security import decode_token
from app.db.models import User
from app.db.session import SessionLocal
from app.schemas.api import ChatRequest
from app.services.chat_service import process_chat
from app.services.ws_manager import manager

router = APIRouter()


@router.websocket("/ws/chat")
async def live_chat(websocket: WebSocket):
    await websocket.accept()
    origin = websocket.headers.get("origin")
    if origin and origin not in get_settings().cors_origin_list:
        await websocket.close(code=4403)
        return
    try:
        auth_message = await websocket.receive_json()
        if auth_message.get("type") != "auth":
            raise ValueError("Authentication message required")
        user_id = int(decode_token(auth_message.get("access_token", "")))
    except (jwt.PyJWTError, ValueError):
        await websocket.close(code=4401)
        return
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user is None:
            await websocket.close(code=4401)
            return
        await manager.connect(user.id, websocket)
        try:
            while True:
                payload = await websocket.receive_json()
                try:
                    if payload.get("type") != "user_message":
                        raise ValueError("Unsupported message type")
                    chat_request = ChatRequest(
                        message=payload.get("text", ""),
                        conversation_id=payload.get("conversation_id"),
                    )
                except (ValueError, TypeError):
                    await websocket.send_json(
                        {"type": "error", "message": "Invalid chat message"}
                    )
                    continue
                await websocket.send_json({"type": "typing"})
                result = process_chat(
                    db, user, chat_request.message, chat_request.conversation_id
                )
                await websocket.send_json({"type": "assistant_message", **result})
        except WebSocketDisconnect:
            pass
        finally:
            await manager.disconnect(user.id, websocket)
