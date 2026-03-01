from dotenv import load_dotenv
load_dotenv('main.env')
import os

POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://postgres:postgres@localhost:5432/livechat')
KAFKA_SERVER = os.getenv('KAFKA_SERVER', 'localhost:9092').split(',')
RAW_TOPIC = os.getenv('RAW_TOPIC', 'raw')
MAX_SESSIONS = int(os.getenv('MAX_SESSIONS', '3'))
EMOJI_MODE = os.getenv('EMOJI_MODE', 'TEXT')
PLAYWRIGHT_SERVER_URL = os.getenv('PLAYWRIGHT_SERVER_URL', 'ws://localhost:3333')
