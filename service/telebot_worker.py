from threading import Thread
from logging_utils import LOGGER
from telebot_handler import TelebotHandler

class TelebotWorker(Thread):

    def __init__(self):
        Thread.__init__(self)

    def run(self):

        try:
            th = TelebotHandler()
            th.run()
            
        except Exception as e: 
            LOGGER.exception(e) 