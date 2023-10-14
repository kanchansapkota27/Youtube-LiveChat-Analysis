from dotenv import load_dotenv
load_dotenv('main.env')
import os



KAFKA_SERVER = os.getenv('KAFKA_SERVER').split(',') if os.getenv('KAFKA_SERVER') else []
RAW_TOPIC = os.getenv('TRANSFORM_CONSUME_TOPIC')
ANALYZED_TOPIC = os.getenv('TRANSFORM_PRODUCE_TOPIC')

    


