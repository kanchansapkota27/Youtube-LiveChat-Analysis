from live import LiveTracker
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    handlers=[
                        logging.FileHandler('app.log',encoding='utf-8'),
                        logging.StreamHandler()
                    ])

logger=logging.getLogger(__name__)

if __name__=='__main__':
        tracker=LiveTracker(link='https://www.youtube.com/watch?v=TPcmrPrygDc',headless=False)
        tracker.track()
