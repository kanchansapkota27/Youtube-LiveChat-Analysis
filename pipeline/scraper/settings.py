from dotenv import load_dotenv
load_dotenv('main.env')
import os
from pprint import pprint


VIDEO_URL= os.getenv('VIDEO_URL')
HEADLESS=os.getenv("HEADLESS") 
EMOJI_MODE = os.getenv('EMOJI_MODE') 
TRACK_TIME_IN_MINUTES = os.getenv('TRACK_TIME_IN_MINUTES') 
KAFKA_SERVER = os.getenv('KAFKA_SERVER').split(',') if os.getenv('KAFKA_SERVER') else []
RAW_TOPIC = os.getenv('EXTRACT_PRODUCE_TOPIC')

print('Loaded Settings:')
pprint({
    'VIDEO_URL':VIDEO_URL,
    'KAFKA_SERVER':KAFKA_SERVER,
    'RAW_TOPIC':RAW_TOPIC,
    'HEADLESS':HEADLESS
})







    


