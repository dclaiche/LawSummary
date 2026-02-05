import asyncio
import secrets

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from app.models.schemas import CaseRequest, CaseResponse, FinalResult, PasswordRequest, PasswordResponse
from app.models.events import StreamEvent, EventType
from app.core.run_store import run_store, RunState
from app.core.sse_manager import sse_manager
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.post("/validate-password", response_model=PasswordResponse)
async def validate_password(req: PasswordRequest):
    is_valid = secrets.compare_digest(req.password, settings.analyze_password)
    return PasswordResponse(valid=is_valid)


@router.post("/case", response_model=CaseResponse)
async def create_case(req: CaseRequest, background_tasks: BackgroundTasks):
    run = run_store.create_run(req.text)
    background_tasks.add_task(_run_pipeline, run)
    return CaseResponse(run_id=run.run_id)


@router.get("/case/{run_id}/stream")
async def stream_case(run_id: str):
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    queue = sse_manager.subscribe(run_id)

    async def event_generator():
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield sse_manager.format_event(event)
        finally:
            sse_manager.unsubscribe(run_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/case/{run_id}", response_model=FinalResult)
async def get_case(run_id: str):
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status == "error":
        raise HTTPException(status_code=500, detail=run.error or "Pipeline failed")
    return run.to_final_result()


async def _run_pipeline(run: RunState) -> None:
    """Execute the agent pipeline. Will be replaced with real orchestration."""
    from app.agents.master_agent import run_master_pipeline

    try:
        run.status = "running"
        await run_master_pipeline(run)
        run.status = "complete"
    except Exception as e:
        run.status = "error"
        run.error = str(e)
        await sse_manager.emit(
            run.run_id,
            StreamEvent(type=EventType.ERROR, payload={"message": str(e)}),
        )
    finally:
        await sse_manager.close(run.run_id)
