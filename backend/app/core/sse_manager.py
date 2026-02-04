import asyncio
import json
from collections import defaultdict

from app.models.events import StreamEvent


class SSEManager:
    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[StreamEvent | None]]] = defaultdict(list)

    def subscribe(self, run_id: str) -> asyncio.Queue[StreamEvent | None]:
        queue: asyncio.Queue[StreamEvent | None] = asyncio.Queue()
        self._queues[run_id].append(queue)
        return queue

    def unsubscribe(self, run_id: str, queue: asyncio.Queue[StreamEvent | None]) -> None:
        if run_id in self._queues:
            self._queues[run_id] = [q for q in self._queues[run_id] if q is not queue]
            if not self._queues[run_id]:
                del self._queues[run_id]

    async def emit(self, run_id: str, event: StreamEvent) -> None:
        for queue in self._queues.get(run_id, []):
            await queue.put(event)

    async def close(self, run_id: str) -> None:
        for queue in self._queues.get(run_id, []):
            await queue.put(None)

    @staticmethod
    def format_event(event: StreamEvent) -> str:
        data = json.dumps({"type": event.type.value, "payload": event.payload})
        return f"data: {data}\n\n"


sse_manager = SSEManager()
