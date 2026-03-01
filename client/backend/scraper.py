"""
Async Playwright scraper that runs as an asyncio Task inside FastAPI.
One task per session; cancelled via task.cancel() on pause/stop/delete.
"""
import asyncio
import logging
import orjson
import yt_dlp
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Inline dataclasses (avoid importing from pipeline path)
# ---------------------------------------------------------------------------
from dataclasses import dataclass, asdict, field


@dataclass
class VideoStaticInfo:
    channel_name: str
    channel_url: str
    channel_category: str
    video_id: str
    video_title: str
    video_url: str
    video_thumbnail_url: str
    is_live: bool
    session_id: str = ''
    info_type: str = 'VIDEO_STATIC_INFO'
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())

    def to_json(self) -> bytes:
        return orjson.dumps(asdict(self))


@dataclass
class VideoLiveMessage:
    video_id: str
    viewers_count: int
    is_live: bool
    message_time_usec: int
    message_author_name: str = ''
    message_content: str = ''
    session_id: str = ''
    inferred_sentiment: Optional[str] = ''
    has_profanity: Optional[bool] = False
    message_dt: Optional[str] = None
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    info_type: str = 'VIDEO_LIVE_MESSAGE'

    def __post_init__(self):
        if self.message_dt is None:
            ts = self.message_time_usec // 1_000_000
            us = self.message_time_usec % 1_000_000
            self.message_dt = datetime.fromtimestamp(ts).replace(microsecond=us).isoformat()

    def to_json(self) -> bytes:
        return orjson.dumps(asdict(self))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_video_info(video_url: str) -> dict:
    """Blocking yt-dlp call — run in executor."""
    with yt_dlp.YoutubeDL({}) as ydl:
        return ydl.extract_info(video_url, download=False)


def _handle_emoji(message_run: dict, emoji_mode: str) -> str:
    emoji = message_run.get('emoji', {})
    if emoji_mode.upper() == 'TEXT' or emoji.get('isCustomEmoji'):
        shortcuts = emoji.get('shortcuts') or emoji.get('shortCuts') or ['']
        return shortcuts[0]
    return emoji.get('emojiId', '')


def _parse_chat_actions(actions: list, video_id: str, session_id: str,
                         live_view_count, is_live: bool, emoji_mode: str):
    """Extract VideoLiveMessage objects from a list of YouTube chat actions."""
    messages = []
    add_actions = [a for a in actions if 'addChatItemAction' in a]
    for chat in add_actions:
        item = chat.get('addChatItemAction', {}).get('item')
        if item is None:
            continue
        renderer = item.get('liveChatTextMessageRenderer')
        if renderer is None:
            continue
        runs = (renderer.get('message') or {}).get('runs')
        if runs is None:
            continue
        author_name_obj = renderer.get('authorName')
        if author_name_obj is None:
            continue
        message_text = ' '.join(
            txt.get('text') or _handle_emoji(txt, emoji_mode)
            for txt in runs
        )
        author = author_name_obj.get('simpleText', '')
        ts_usec = renderer.get('timestampUsec')
        if ts_usec is None:
            continue
        messages.append(VideoLiveMessage(
            message_time_usec=int(ts_usec),
            message_author_name=author,
            message_content=message_text,
            video_id=video_id,
            viewers_count=live_view_count,
            is_live=is_live,
            session_id=session_id,
        ))
    return messages


# ---------------------------------------------------------------------------
# Main async scraper task
# ---------------------------------------------------------------------------

async def run_scraper_session(
    session_id: str,
    video_url: str,
    kafka_producer,       # sync kafka-python KafkaProducer
    raw_topic: str,
    browser,              # shared Playwright Browser instance
    pool,                 # asyncpg Pool — for updating session metadata
    emoji_mode: str = 'TEXT',
) -> None:
    """
    Async scraper task. Intercepts YouTube's /youtubei/v1/* internal API
    calls to extract live chat messages and viewer counts, publishing each
    to Kafka. Designed to be cancelled via task.cancel().
    """
    loop = asyncio.get_event_loop()

    # --- Fetch video metadata (blocking yt-dlp) ---
    try:
        info = await loop.run_in_executor(None, _get_video_info, video_url)
    except Exception as e:
        logger.error(f'[{session_id}] Failed to fetch video info: {e}', exc_info=True)
        await pool.execute("UPDATE sessions SET status='stopped' WHERE session_id=$1", session_id)
        return

    if not info.get('is_live'):
        logger.error(f'[{session_id}] Video is not live: {video_url}')
        await pool.execute("UPDATE sessions SET status='stopped' WHERE session_id=$1", session_id)
        return

    video_id = info.get('id', '')
    static_info = VideoStaticInfo(
        channel_name=info.get('channel', ''),
        channel_url=info.get('channel_url', ''),
        channel_category='',
        video_id=video_id,
        video_title=info.get('fulltitle', ''),
        video_url=video_url,
        video_thumbnail_url=info.get('thumbnail', ''),
        is_live=True,
        session_id=session_id,
    )

    # Update session row with video metadata and transition to active
    await pool.execute(
        """
        UPDATE sessions
        SET video_id=$1, video_title=$2, channel_name=$3, thumbnail_url=$4, status='active'
        WHERE session_id=$5
        """,
        video_id,
        info.get('fulltitle', ''),
        info.get('channel', ''),
        info.get('thumbnail', ''),
        session_id,
    )
    logger.info(f'[{session_id}] Session active, video_id={video_id}')

    # Publish static info
    await loop.run_in_executor(None, kafka_producer.send, raw_topic, static_info.to_json())
    logger.info(f'[{session_id}] Published VideoStaticInfo for video_id={video_id}')

    # --- Open browser context ---
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    )
    page = await context.new_page()

    live_view_count = info.get('concurrent_view_count') or 0
    is_live = True

    # Queue to bridge the event-driven response listener into the async loop
    response_queue: asyncio.Queue = asyncio.Queue()

    def on_response(response):
        if 'youtubei/v1/' in response.url:
            asyncio.ensure_future(response_queue.put(response))

    page.on('response', on_response)

    try:
        await page.goto(video_url)
        logger.info(f'[{session_id}] Browser navigated to {video_url}')

        while True:
            try:
                response = await asyncio.wait_for(response_queue.get(), timeout=60.0)
                url = response.url
                raw_data = await response.body()
            except asyncio.TimeoutError:
                logger.warning(f'[{session_id}] No YouTubei API response received in 60s, continuing...')
                continue
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(f'[{session_id}] Response wait error: {e}')
                continue

            try:
                data = orjson.loads(raw_data)
            except Exception:
                continue

            # ---- Live chat messages ----
            logger.info(f'[{session_id}] Intercepted API call: {url}')
            if 'get_live_chat' in url:
                continuation = (data.get('continuationContents') or {})
                actions = (continuation.get('liveChatContinuation') or {}).get('actions')
                if actions:
                    msgs = _parse_chat_actions(
                        actions, video_id, session_id,
                        live_view_count, is_live, emoji_mode
                    )
                    logger.info(f'[{session_id}] Extracted {len(msgs)} chat messages from API response.')
                    for msg in msgs:
                        await loop.run_in_executor(
                            None, kafka_producer.send, raw_topic, msg.to_json()
                        )
                        logger.info(f'[{session_id}] Sent: {msg.message_author_name}: {msg.message_content[:40]}')

            # ---- Viewer count updates ----
            elif 'updated_metadata' in url:
                logger.info(f'[{session_id}] Checking for viewer count in API response...')
                actions = data.get('actions') or []
                for item in actions:
                    view_action = item.get('updateViewershipAction')
                    if not view_action:
                        continue
                    renderer = (view_action.get('viewCount') or {}).get('videoViewCountRenderer') or {}
                    if not renderer.get('isLive'):
                        is_live = False
                        continue
                    raw_count = str(renderer.get('originalViewCount', '0')).replace(',', '')
                    try:
                        live_view_count = int(raw_count)
                    except ValueError:
                        pass
                    is_live = True

    except asyncio.CancelledError:
        logger.info(f'[{session_id}] Scraper task cancelled (pause/stop/delete)')
    except Exception as e:
        logger.error(f'[{session_id}] Unexpected scraper error: {e}', exc_info=True)
    finally:
        page.remove_listener('response', on_response)
        try:
            await loop.run_in_executor(None, kafka_producer.flush)
        except Exception:
            pass
        await context.close()
        logger.info(f'[{session_id}] Scraper cleaned up.')