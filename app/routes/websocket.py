import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.utils.logger import logger

router = APIRouter(tags=["WebSocket - Live Order Tracking"])


class ConnectionManager:

    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}
        self.loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

    async def connect(self, order_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(order_id, []).append(websocket)

    def disconnect(self, order_id: int, websocket: WebSocket) -> None:
        if order_id in self.active_connections:
            if websocket in self.active_connections[order_id]:
                self.active_connections[order_id].remove(websocket)
            if not self.active_connections[order_id]:
                del self.active_connections[order_id]

    async def broadcast(self, order_id: int, message: dict) -> None:
        for connection in self.active_connections.get(order_id, []):
            try:
                await connection.send_json(message)
            except Exception as error:
                logger.error(f"WebSocket send failed : {str(error)}")


manager = ConnectionManager()


@router.websocket("/ws/orders/{order_id}")
async def order_tracking_socket(websocket: WebSocket, order_id: int):
    await manager.connect(order_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(order_id, websocket)


# called from synchronous service functions - hands the broadcast off
# to the real event loop safely, same proven fix carried forward from
# every previous project's websocket feature
def broadcast_order_update_sync(order_id: int, message: dict) -> None:

    if manager.loop is None:
        logger.error("WebSocket broadcast skipped : event loop not yet available.")
        return

    try:
        asyncio.run_coroutine_threadsafe(manager.broadcast(order_id, message), manager.loop)
    except Exception as error:
        logger.error(f"WebSocket broadcast failed : {str(error)}")