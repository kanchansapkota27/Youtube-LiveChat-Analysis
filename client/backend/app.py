"""
FastAPI backend -- session management + per-session SSE streams.
Uses asyncpg (PostgreSQL) for storage and LISTEN/NOTIFY for real-time SSE.
"""
import asyncio
import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional

import asyncpg
import emoji
import settings
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaProducer
from playwright.async_api import async_playwright
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from scraper import run_scraper_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global state -- populated in lifespan
# ---------------------------------------------------------------------------
active_tasks: dict[str, asyncio.Task] = {}
_playwright = None
_browser = None
_producer: Optional[KafkaProducer] = None
_pool: Optional[asyncpg.Pool] = None


def _row(record) -> Optional[dict]:
    """Convert asyncpg Record to a JSON-safe dict (handles datetime, Decimal)."""
    if record is None:
        return None
    result = {}
    for key, value in record.items():
        if isinstance(value, (datetime, date)):
            result[key] = value.isoformat()
        elif isinstance(value, Decimal):
            result[key] = float(value)
        else:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(application: FastAPI):
    global _playwright, _browser, _producer, _pool

    _pool = await asyncpg.create_pool(settings.POSTGRES_URL, min_size=2, max_size=10)
    logger.info(f"Connected to PostgreSQL: {settings.POSTGRES_URL}")

    # Recover interrupted sessions on restart
    await _pool.execute(
        "UPDATE sessions SET status='paused', paused_at=now() WHERE status='active'"
    )
    await _pool.execute(
        "UPDATE sessions SET status='stopped' WHERE status='fetching'"
    )

    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.connect(settings.PLAYWRIGHT_SERVER_URL)
    logger.info(f"Playwright connected to remote browser: {settings.PLAYWRIGHT_SERVER_URL}")

    try:
        _producer = KafkaProducer(bootstrap_servers=settings.KAFKA_SERVER)
        logger.info(f"Kafka producer connected: {settings.KAFKA_SERVER}")
    except Exception as e:
        logger.error(f"Cannot connect to Kafka: {e}")
        _producer = None

    yield

    logger.info("Shutting down...")
    for task in list(active_tasks.values()):
        task.cancel()
    if active_tasks:
        await asyncio.gather(*active_tasks.values(), return_exceptions=True)
    if _producer:
        _producer.close()
    if _browser:
        await _browser.close()
    if _playwright:
        await _playwright.stop()
    if _pool:
        await _pool.close()
    logger.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateSessionRequest(BaseModel):
    video_url: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _start_scraper_task(session_id: str, video_url: str):
    if _producer is None:
        raise HTTPException(status_code=503, detail="Kafka not available")
    task = asyncio.create_task(
        run_scraper_session(
            session_id=session_id,
            video_url=video_url,
            kafka_producer=_producer,
            raw_topic=settings.RAW_TOPIC,
            browser=_browser,
            pool=_pool,
            emoji_mode=settings.EMOJI_MODE,
        ),
        name=f"scraper-{session_id}",
    )
    active_tasks[session_id] = task
    task.add_done_callback(lambda t: active_tasks.pop(session_id, None))
    logger.info(f"Started scraper task for session {session_id}")


async def _cancel_task(session_id: str):
    task = active_tasks.pop(session_id, None)
    if task and not task.done():
        task.cancel()
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=5.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
    logger.info(f"Cancelled scraper task for session {session_id}")


# ---------------------------------------------------------------------------
# Session routes
# ---------------------------------------------------------------------------

@app.get("/sessions")
async def list_sessions():
    rows = await _pool.fetch(
        "SELECT * FROM sessions WHERE status != 'deleted' ORDER BY created_at DESC"
    )
    return [_row(r) for r in rows]


@app.post("/sessions", status_code=201)
async def create_session(body: CreateSessionRequest):
    count = await _pool.fetchval(
        "SELECT COUNT(*) FROM sessions WHERE status IN ('active', 'paused', 'fetching')"
    )
    if count >= settings.MAX_SESSIONS:
        raise HTTPException(
            status_code=409,
            detail=f"Session limit reached ({settings.MAX_SESSIONS}). Delete a session first.",
        )
    session_id = str(uuid.uuid4())
    row = await _pool.fetchrow(
        """
        INSERT INTO sessions (session_id, video_url, status, created_at)
        VALUES ($1, $2, 'fetching', now())
        RETURNING *
        """,
        session_id, body.video_url,
    )
    _start_scraper_task(session_id, body.video_url)
    return _row(row)


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    row = await _pool.fetchrow(
        "SELECT * FROM sessions WHERE session_id=$1", session_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    return _row(row)


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    row = await _pool.fetchrow(
        "SELECT session_id FROM sessions WHERE session_id=$1", session_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    await _cancel_task(session_id)
    await _pool.execute(
        "UPDATE sessions SET status='deleted', deleted_at=now() WHERE session_id=$1",
        session_id,
    )
    result = await _pool.execute(
        "UPDATE chats SET is_archived=TRUE WHERE session_id=$1 AND NOT is_archived",
        session_id,
    )
    logger.info(f"Archived chats for session {session_id}: {result}")
    return {"detail": "Session deleted and chats archived"}


@app.put("/sessions/{session_id}/pause")
async def pause_session(session_id: str):
    row = await _pool.fetchrow(
        "SELECT status FROM sessions WHERE session_id=$1", session_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    if row["status"] != "active":
        raise HTTPException(status_code=409, detail="Session is not active")
    await _cancel_task(session_id)
    updated = await _pool.fetchrow(
        """
        UPDATE sessions
        SET status='paused', paused_at=now(), last_checkpoint=now()
        WHERE session_id=$1
        RETURNING *
        """,
        session_id,
    )
    return _row(updated)


@app.put("/sessions/{session_id}/resume")
async def resume_session(session_id: str):
    row = await _pool.fetchrow(
        "SELECT status, video_url FROM sessions WHERE session_id=$1", session_id
    )
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    if row["status"] not in ("paused", "stopped"):
        raise HTTPException(status_code=409, detail="Session is not paused")
    _start_scraper_task(session_id, row["video_url"])
    updated = await _pool.fetchrow(
        "UPDATE sessions SET status='active', resumed_at=now() WHERE session_id=$1 RETURNING *",
        session_id,
    )
    return _row(updated)


# ---------------------------------------------------------------------------
# Chat routes
# ---------------------------------------------------------------------------

@app.get("/sessions/{session_id}/chats")
async def get_session_chats(session_id: str, limit: int = 500):
    """Return non-archived chats for a session, oldest-first."""
    rows = await _pool.fetch(
        """
        SELECT * FROM chats
        WHERE session_id=$1 AND NOT is_archived
        ORDER BY message_time_usec ASC NULLS LAST
        LIMIT $2
        """,
        session_id, limit,
    )
    return [_row(r) for r in rows]


# ---------------------------------------------------------------------------
# SSE stream — PostgreSQL LISTEN/NOTIFY
# ---------------------------------------------------------------------------

async def _session_stream(session_id: str, request: Request):
    conn = await asyncpg.connect(settings.POSTGRES_URL)
    queue: asyncio.Queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def _on_notify(connection, pid, channel, payload):
        loop.call_soon_threadsafe(queue.put_nowait, payload)

    await conn.add_listener(f'chat_{session_id}', _on_notify)
    try:
        while True:
            if await request.is_disconnected():
                break
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=30.0)
                if settings.EMOJI_MODE == 'EMOJI':
                    data = json.loads(payload)
                    data['message_content'] = emoji.emojize(
                        data.get('message_content', ''), language='alias'
                    )
                    payload = json.dumps(data)
                yield {"data": payload, "event": "message"}
            except asyncio.TimeoutError:
                yield {"data": "", "event": "ping"}  # keepalive
    finally:
        await conn.remove_listener(f'chat_{session_id}', _on_notify)
        await conn.close()


@app.get("/stream/{session_id}")
async def stream_session(session_id: str, request: Request):
    return EventSourceResponse(_session_stream(session_id, request))


# ---------------------------------------------------------------------------
# Video info
# ---------------------------------------------------------------------------

@app.get("/video/{video_id}")
async def get_video(video_id: str):
    row = await _pool.fetchrow(
        "SELECT * FROM video_info WHERE video_id=$1 ORDER BY recorded_at DESC LIMIT 1",
        video_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Video info not found")
    return _row(row)


if __name__ == "__main__":
    uvicorn.run("app:app", port=3000, reload=True)
