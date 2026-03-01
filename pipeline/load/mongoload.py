import psycopg2
from kafka import KafkaConsumer
import orjson
import settings
import logging
import typer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('loader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = typer.Typer()


class PgLoader:
    def __init__(self) -> None:
        self.server = settings.KAFKA_SERVER
        self.postgres_url = settings.POSTGRES_URL

    def init_db(self):
        self.conn = psycopg2.connect(self.postgres_url)
        self.conn.autocommit = False
        logger.info('Connected to PostgreSQL.')

    def __start_consumer(self):
        consume_topic = settings.ANALYZED_TOPIC
        self.consumer = KafkaConsumer(
            consume_topic,
            bootstrap_servers=self.server,
            group_id='loader-group',
        )
        logger.info(f'Started Kafka Consumer on topic: {consume_topic}')

    def receive_upstream(self):
        for message in self.consumer:
            yield message.value

    def push_chat(self, msg: dict):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chats (
                    session_id, video_id, message_author_name, message_content,
                    message_dt, message_time_usec, inferred_sentiment,
                    has_profanity, viewers_count, is_live
                ) VALUES (%s, %s, %s, %s, %s::timestamptz, %s, %s, %s, %s, %s)
                """,
                (
                    msg.get('session_id'),
                    msg.get('video_id', ''),
                    msg.get('message_author_name', ''),
                    msg.get('message_content', ''),
                    msg.get('message_dt'),
                    msg.get('message_time_usec'),
                    msg.get('inferred_sentiment'),
                    msg.get('has_profanity', False),
                    msg.get('viewers_count', 0),
                    msg.get('is_live', True),
                ),
            )
        self.conn.commit()
        logger.info(f"Inserted chat: {msg.get('message_author_name')}: {msg.get('message_content', '')[:40]}")

    def push_video_info(self, msg: dict):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO video_info (
                    session_id, video_id, channel_name, channel_url,
                    video_title, video_url, thumbnail_url, is_live
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    msg.get('session_id'),
                    msg.get('video_id', ''),
                    msg.get('channel_name', ''),
                    msg.get('channel_url', ''),
                    msg.get('video_title', ''),
                    msg.get('video_url', ''),
                    msg.get('video_thumbnail_url', ''),
                    msg.get('is_live', False),
                ),
            )
        self.conn.commit()
        logger.info(f"Inserted video_info for video_id={msg.get('video_id')}")

    def __start_session(self):
        self.init_db()
        self.__start_consumer()
        for message in self.receive_upstream():
            try:
                json_message = orjson.loads(message)
                message_type = json_message.get('info_type')
                if message_type == 'VIDEO_LIVE_MESSAGE':
                    self.push_chat(json_message)
                elif message_type == 'VIDEO_STATIC_INFO':
                    self.push_video_info(json_message)
            except Exception as e:
                logger.error(f'Failed to process message: {e}', exc_info=True)
                self.conn.rollback()

    def load(self):
        try:
            self.__start_session()
        except Exception as e:
            logger.error(e, exc_info=True)


@app.command()
def run():
    loader = PgLoader()
    loader.load()


if __name__ == '__main__':
    app()
