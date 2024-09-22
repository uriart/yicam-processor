from threading import Thread
from logging_utils import LOGGER
from mosquitto_consumer import MosquittoConsumer

class MqttWorker(Thread):

    def __init__(self):
        Thread.__init__(self)

    def run(self):

        try:
            mc = MosquittoConsumer()
            mc.setup_mqtt()
            
        except Exception as e: 
            LOGGER.exception(e) 