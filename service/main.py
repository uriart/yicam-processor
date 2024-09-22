#!/usr/bin/env python
import os
import sys
from mqtt_worker import MqttWorker
from telebot_worker import TelebotWorker

def main():
    
    mqtt_worker = MqttWorker()
    mqtt_worker.daemon = True
    mqtt_worker.start()

    telebot_worker = TelebotWorker()
    telebot_worker.daemon = True
    telebot_worker.start()

    telebot_worker.join()
    mqtt_worker.join()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)