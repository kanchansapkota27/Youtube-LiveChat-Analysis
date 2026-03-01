from dataclasses import dataclass, asdict, field
import orjson
from datetime import datetime
from enum import Enum
from typing import Optional


class InfoType(Enum):
    VIDEO_STATIC_INFO = 'VIDEO_STATIC_INFO'
    VIDEO_LIVE_INFO = 'VIDEO_LIVE_INFO'
    VIDEO_LIVE_MESSAGE = 'VIDEO_LIVE_MESSAGE'


class SentimentType(Enum):
    POSITIVE = 'POS'
    NEGATIVE = 'NEG'
    NEUTRAL = 'NEU'


@dataclass
class BaseDataClass:

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return orjson.dumps(asdict(self))


@dataclass
class VideoStaticInfo(BaseDataClass):
    channel_name: str
    channel_url: str
    channel_category: str
    video_id: str
    video_title: str
    video_url: str
    video_thumbnail_url: str
    is_live: bool
    session_id: str = ''
    info_type: str = InfoType.VIDEO_STATIC_INFO.value
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())


@dataclass
class VideoLiveMessage(BaseDataClass):
    # Required fields — no defaults
    video_id: str
    viewers_count: int = field(repr=False)
    is_live: bool = field(repr=False)
    message_time_usec: int = field(repr=False)
    # Optional fields — have defaults (must come after required)
    message_author_name: str = ''
    message_content: str = ''
    session_id: str = ''
    inferred_sentiment: Optional[str] = ''
    has_profanity: Optional[bool] = False
    message_dt: Optional[str] = field(default=None, repr=False)
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    info_type: str = InfoType.VIDEO_LIVE_MESSAGE.value

    def format_timestamp(self):
        timestamp_seconds = self.message_time_usec // 1000000
        microsecond = self.message_time_usec % 1000000
        dt = datetime.fromtimestamp(timestamp_seconds).replace(microsecond=microsecond)
        self.message_dt = dt.isoformat()

    def __post_init__(self):
        if self.message_dt is None:
            self.format_timestamp()

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__qualname__} '
            f'author={self.message_author_name} '
            f'message={self.message_content} '
            f'time={self.message_dt}>'
        )
