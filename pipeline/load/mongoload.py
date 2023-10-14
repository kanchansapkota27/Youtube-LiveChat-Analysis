from kafka import KafkaConsumer
from pymongo import MongoClient
import orjson
import settings
from pprint import pprint
import logging
import sys
import typer
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    handlers=[
                        logging.FileHandler('loader.log'),
                        logging.StreamHandler()
                    ])


logger = logging.getLogger(__name__)

app=typer.Typer()


# Connect to MongoDB and pizza_data database
logger=logging.getLogger(__name__)

class MongoLoader:
    def __init__(self) -> None:
        self.server=settings.KAFKA_SERVER
        self.connection_url=settings.MONGO_DB_URL
   
    def init_db(self):
        client = MongoClient(self.connection_url)
        self.client=client
        
        try:
            client.admin.command('ping')
            logger.info('Ping db successfully.')
        except Exception as e:
            logger.exception(e,stack_info=True)
            exit(1)
        db=self.client.main
        self.db=db

    def __start_consumer(self):
        consume_topic=settings.ANALYZED_TOPIC
        self.consumer=KafkaConsumer(consume_topic,bootstrap_servers=self.server)
        logger.info(f'Started Kafka Consumer on topic :{consume_topic}')

    def recieve_upstream(self):
        for message in self.consumer:
            raw_message=message.value
            yield raw_message

    def push_to_db(self,json_message,collection_name):
        if collection_name not in self.db.list_collection_names():
            self.db.create_collection(collection_name)
        
        collection=self.db.get_collection(collection_name)
        response=collection.insert_one(json_message)
        logger.info(f'Inserted message with ID of:{response.inserted_id}')
        return response.inserted_id
    
    def __start_session(self):
        self.init_db()
        self.__start_consumer()
        for message in self.recieve_upstream():
            json_message=orjson.loads(message)
            message_type=json_message['info_type']
            if message_type=='VIDEO_STATIC_INFO':
                self.push_to_db(json_message,'info')
            if message_type=='VIDEO_LIVE_MESSAGE':
                self.push_to_db(json_message,'live')
        
    def load(self):
        try:
            self.__start_session()
        except Exception as e:
            print(e)
            logger.error(e)



@app.command()
def run():
    loader=MongoLoader()
    loader.load()


if __name__=='__main__':
    app()


    

