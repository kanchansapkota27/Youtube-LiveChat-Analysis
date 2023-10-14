from typing import Optional
import settings
from exceptions import PlaywrightExecutionError,NotLiveVideoError
import yt_dlp
import logging
import orjson
from datetime import datetime,timedelta
from playwright.sync_api import sync_playwright
from models import VideoStaticInfo,VideoLiveMessage
from kafka import KafkaProducer
import typer


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    handlers=[
                        logging.FileHandler('live.log'),
                        logging.StreamHandler()
                    ])


logger = logging.getLogger(__name__)

app=typer.Typer()



class LiveTracker:
    def __init__(self,link:str=None,headless:str=True) -> None:
        self.ydl_opts={}
        raw_headless=True if settings.HEADLESS.lower().strip() =='true' else False
        self.headless=raw_headless if raw_headless!=None else headless
        print(f'Operating in Headless:{self.headless} Mode')
        session_run_minutes=int(settings.TRACK_TIME_IN_MINUTES)
        self.session_ends_on= datetime.now() + timedelta(minutes=session_run_minutes) if session_run_minutes > 0 else None        
        self.video_link= link if link!=None else settings.VIDEO_URL
        if self.video_link is None:
            logger.error(f'Video Link was not received. Got:{self.video_link}')
            self.is_tracking=False
            exit(1)
        if self.session_ends_on:
            logger.info(f'Session will end on: {self.session_ends_on}')
        self.live_view_count=0
        self.is_live=True
        self.session_video_info=self.get_video_info(video_link=self.video_link)



    def __start_session(self):
        if not self.session_video_info.is_live:
            raise NotLiveVideoError
        self.producer=self.__start_producer()
        self.playwright=sync_playwright().start()
        self.is_tracking=True
        send_topic=settings.RAW_TOPIC
        self.producer.send(send_topic,self.session_video_info.to_json())
        self.browser=self.playwright.chromium.launch(headless=self.headless)
        page=self.browser.new_page()
        # page.goto(f'https://www.youtube.com/live_chat?is_popout=1&v={self.session_video_info.video_id}')
        page.goto(self.video_link)
        self.page=page

    def __end_session(self):
        try:
            if self.playwright and self.browser:
                self.browser.close()
                self.playwright.stop()
        except AttributeError:
            pass
        self.playwright=None
        self.browser=None
        self.page=None
        self.is_tracking=False
        self.session_video_info=None
        self.producer.close()


    def __start_producer(self):
        try:
            server=settings.KAFKA_SERVER
            producer=KafkaProducer(bootstrap_servers=server)
            return producer
        except Exception as e:
            print(f'Cannot connect to producer.Encountered Error:\n\t{e}')
            logger.error('Cannot connect to the producer',e)
            exit(1)



    def get_video_info(self,video_link):
        logger.info(f'Fetching information for URL:{video_link}')
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            info=ydl.extract_info(video_link,download=False)
            channel_name=info.get('channel')
            channel_url=info.get('channel_url')
            watching_now=info.get('concurrent_view_count')
            self.initial_live=int(watching_now) if watching_now else None
            video_title=info.get('fulltitle')
            video_id=info.get('id')
            is_live=info.get('is_live')
            self.live_view_count=watching_now
            self.is_live=is_live
            thumbnail=info.get('thumbnail')
            video_info=VideoStaticInfo(
                channel_name=channel_name,
                channel_url=channel_url,
                channel_category='',
                video_id=video_id,
                video_title=video_title,
                video_url=video_link,
                video_thumbnail_url=thumbnail,
                is_live=is_live
            )
            return video_info
        

    def __handle_get_emoji(self,message_run):
        emoji=message_run.get('emoji')
        if settings.EMOJI_MODE=='TEXT' or emoji.get('isCustomEmoji'):
            return emoji.get('shorcuts',[''])[0]
        else:
            return emoji.get('emojiId')



    def __start_livechat_track(self):
        while self.is_tracking:
            with self.page.expect_response("https://www.youtube.com/youtubei/v1/*") as response:
                response=response.value
                url=response.url
                raw_data=response.body()
                data=orjson.loads(raw_data)
                if 'live_chat/get_live_chat' in url:
                    actions=data.get('continuationContents').get('liveChatContinuation').get('actions')
                    if actions is None:
                        continue
                    addChatActions=[item for item in actions if 'addChatItemAction' in item]
                    for chat in addChatActions:
                        one_action=chat.get("addChatItemAction")
                        item=one_action.get('item')
                        if item is None:
                            break
                        liveChatData=item.get('liveChatTextMessageRenderer')
                        if liveChatData is None:
                            break
                        message=' '.join([txt.get('text') or self.__handle_get_emoji(txt) for txt  in liveChatData.get('message').get('runs')])
                        author=liveChatData.get('authorName').get('simpleText')
                        timestampUsec=liveChatData.get('timestampUsec')
                        timestamp=int(timestampUsec)
                        cleanchat=VideoLiveMessage(
                            message_time_usec=timestamp,
                            message_author_name=author,
                            message_content=message,
                            video_id=self.session_video_info.video_id,
                            viewers_count=self.live_view_count,
                            is_live=self.is_live
                            )
                        yield cleanchat
                if 'updated_metadata' in url:
                    actions=data.get('actions')
                    if actions is None:
                        continue
                    viewActions=[item for item in actions if 'updateViewershipAction' in item]
                    for viewEvent in viewActions:
                        one_data=viewEvent.get('updateViewershipAction').get('viewCount')
                        item=one_data.get('videoViewCountRenderer')
                        isLive=item.get('isLive')
                        if not isLive:
                            break
                        view_count=item.get('originalViewCount')
                        view_count=str(view_count).replace(',','')
                        self.live_view_count=int(view_count)
                        self.is_live=isLive

            if self.session_ends_on and self.session_ends_on <=datetime.now():
                self.is_tracking=False
                

    def track(self):
                try:
                    self.__start_session()
                    if self.browser==None or self.page==None :
                        raise PlaywrightExecutionError(f'Unable to get browser ,Got:{self.browser}')
                    #Referenced URL for Code: https://stackoverflow.com/questions/47456631/simpler-way-to-run-a-generator-function-without-caring-about-items
                    # deque(self.__start_livechat_track(),maxlen=1)
                    send_topic=settings.RAW_TOPIC
                    # self.page.screenshot(path='/screenshots')
                    for live_chat_message in self.__start_livechat_track():
                        message=live_chat_message.to_json()
                        # print(message)
                        logger.info(f'Sent Message: {live_chat_message}')
                        # print(live_chat_message)
                        self.producer.send(send_topic,message)
                        self.producer.flush(1)
                    self.__end_session()
                except NotLiveVideoError as e:
                    print(f'The provided video is not a live video:{e}')
                    logger.error('Video Link provided is not a live video',stack_info=True)
                except PlaywrightExecutionError:
                    print(f'Something went wrong with playwright:{e}')
                    logger.error('Something went wrong with Playwright',stack_info=True)
            

@app.command()
# def run(url:Annotated[Optional[str], typer.Argument(envvar="VIDEO_URL")]=None,headless:bool=True):
def run(url:Optional[str]=None,headless:bool=True):
    track=LiveTracker(link=url,headless=headless)
    track.track()


if __name__=='__main__':
    app()
        