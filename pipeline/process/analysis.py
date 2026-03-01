import settings
from models import VideoLiveMessage, SentimentType
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from kafka import KafkaProducer, KafkaConsumer
import orjson
import logging
import typer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('process.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = typer.Typer()


class Analyser:
    def __init__(self, sentiment: bool = True, profanity: bool = False) -> None:
        self.server = settings.KAFKA_SERVER
        self.consume_topic = settings.RAW_TOPIC
        self.produce_topic = settings.ANALYZED_TOPIC
        self.enable_sentiment = sentiment
        self.enable_profanity = profanity

    def __start_consumer(self):
        self.consumer = KafkaConsumer(
            self.consume_topic,
            bootstrap_servers=self.server,
            group_id='processor-group',
        )
        logger.info(f'Started Analyser consuming on topic: {self.consume_topic}')

    def __start_producer(self):
        self.producer = KafkaProducer(bootstrap_servers=self.server)
        logger.info(f'Started Producer producing on topic: {self.produce_topic}')

    def __start_analyzers(self):
        if self.enable_sentiment:
            self.sentiment = SentimentIntensityAnalyzer()

    def __start_session(self):
        self.__start_consumer()
        self.__start_producer()
        self.__start_analyzers()
        for message in self.recieve_upstream():
            processed = self.process_message(raw_message=message)
            if processed:
                self.send_downstream(processed)

    def recieve_upstream(self):
        for message in self.consumer:
            yield message.value

    def get_sentiment(self, message: str) -> str:
        scores = self.sentiment.polarity_scores(message)
        if scores['compound'] >= 0.05:
            return SentimentType.POSITIVE.value
        elif scores['compound'] <= -0.05:
            return SentimentType.NEGATIVE.value
        else:
            return SentimentType.NEUTRAL.value

    def process_message(self, raw_message):
        json_message = orjson.loads(raw_message)
        if json_message.get('info_type') != 'VIDEO_LIVE_MESSAGE':
            # Pass VIDEO_STATIC_INFO and any other types through unchanged
            return raw_message
        message_obj = VideoLiveMessage(**json_message)

        if self.enable_sentiment:
            message_obj.inferred_sentiment = self.get_sentiment(message_obj.message_content)
        else:
            message_obj.inferred_sentiment = SentimentType.NEUTRAL.value

        message_obj.has_profanity = False  # TODO: profanity check

        logger.info(f'Completed analysis for: {message_obj}')
        return message_obj.to_json()

    def send_downstream(self, message):
        self.producer.send(self.produce_topic, message)

    def analyse(self):
        self.__start_session()


@app.command()
def run(sentiment: bool = True, profanity: bool = False):
    process = Analyser(sentiment=sentiment, profanity=profanity)
    process.analyse()


if __name__ == '__main__':
    app()
