from dataclasses import dataclass,asdict,field
import orjson
from datetime import datetime
from enum import Enum
from typing import Optional
from datetime import datetime

class InfoType(Enum):
    VIDEO_STATIC_INFO='VIDEO_STATIC_INFO'
    VIDEO_LIVE_INFO='VIDEO_LIVE_INFO'
    VIDEO_LIVE_MESSAGE='VIDEO_LIVE_MESSAGE'


class SentimentType(Enum):
    POSITIVE='POS'
    NEGATIVE='NEG'
    NEUTRAL='NEU'


@dataclass
class BaseDataClass:

    def to_dict(self):
        return asdict(self)
    
    def to_json(self):
        return orjson.dumps(asdict(self))
    

@dataclass
class VideoStaticInfo(BaseDataClass):
    channel_name:str
    channel_url:str
    channel_category:str
    video_id:str
    video_title:str
    video_url:str
    video_thumbnail_url:str
    is_live:bool
    info_type:str=InfoType.VIDEO_STATIC_INFO
    timestamp:float=datetime.utcnow().timestamp()


@dataclass
class VideoLiveMessage(BaseDataClass):
    video_id:str
    viewers_count:int=field(repr=False)
    is_live:bool=field(repr=False)
    message_time_usec:int=field(repr=False)
    message_dt:datetime=field(repr=False)
    message_author_name:str
    message_content:str
    inferred_sentiment:Optional[str]=''
    has_profanity:Optional[bool]=False
    timestamp:float=datetime.utcnow().timestamp()
    info_type:str=InfoType.VIDEO_LIVE_MESSAGE

    def format_timestamp(self):
        timestamp_seconds = self.message_time_usec // 1000000
        microsecond = self.message_time_usec % 1000000
        self.message_dt = datetime.fromtimestamp(timestamp_seconds).replace(microsecond=microsecond)

    # def __post_init__(self):
    #     self.format_timestamp()


    def __repr__(self) -> str:
        return f'<{self.__class__.__qualname__} author={self.message_author_name}  message={self.message_content} time={self.message_dt}>'
    
    







