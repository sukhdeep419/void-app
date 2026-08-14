import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse

from models import CommandRequest, ConfirmActionRequest
from services.actions import pop_pending_action
from services.agent import generate_groq_stream
from services.system import get_system_metrics
from services.tools import execute_tool

router = APIRouter()


@router.get("/")
def read_root():
    return {"status": "Void Backend Running"}


@router.post("/api/confirm-action")
async def confirm_action(request: ConfirmActionRequest):
    pending = pop_pending_action(request.token)
    if not pending:
        return JSONResponse(
            status_code=404,
            content={
                "message": "This approval request has expired or is no longer available."
            },
        )
    result = execute_tool(pending["name"], pending["arguments"])
    return {"message": result}


@router.post("/api/command")
async def execute_command(request: CommandRequest):
    return StreamingResponse(
        generate_groq_stream(request.messages),
        media_type="text/plain",
    )


@router.websocket("/ws/system")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    async def send_metrics():
        try:
            while True:
                metrics = get_system_metrics()
                await websocket.send_text(json.dumps(metrics))
                await asyncio.sleep(1)
        except Exception:
            pass

    send_task = asyncio.create_task(send_metrics())

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("Client disconnected gracefully")
    except Exception as exc:
        print(f"Error in websocket connection: {exc}")
    finally:
        send_task.cancel()
