from dotenv import load_dotenv
load_dotenv('main.env')
import os

KAFKA_SERVER = os.getenv('KAFKA_SERVER').split(',') if os.getenv('KAFKA_SERVER') else []
ANALYZED_TOPIC = os.getenv('LOAD_CONSUME_TOPIC')
POSTGRES_URL = os.getenv('POSTGRES_URL')
