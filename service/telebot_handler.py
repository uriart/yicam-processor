import telebot
from config import *
from logging_utils import LOGGER
import requests

class TelebotHandler:

    def __init__(self):
        self.bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
        self.bot.message_handler(commands=['help', 'start'])(self.help)
        self.bot.message_handler(commands=['snapshoot'])(self.take_snapshoot)
        self.bot.message_handler(commands=['moveCam'])(self.moveCam)
        self.bot.message_handler(commands=['status'])(self.status)
        self.bot.callback_query_handler(func=lambda call: True)(self.callback_query)

    def run(self):
        LOGGER.info("Telebot handler started.")
        self.bot.infinity_polling()

    def help(self, message):
        if str(message.chat.id) in TELEGRAM_CHAT_IDS:
            help_message = (
                "🌟 **Ayuda del Bot** 🌟\n\n"
                "¡Hola! Aquí tienes una lista de comandos que puedes usar:\n\n"
                "1️⃣ **/help** - Muestra este mensaje de ayuda.\n"
                "2️⃣ **/moveCam** - Apunta la cámara a la ubicación seleccionada.\n"
                "3️⃣ **/snapshoot** - Toma una instantánea de la cámara IP y la envía aquí.\n"
                "3️⃣ **/status** - Estado de la detección de movimiento.\n\n"
            )
            self.bot.reply_to(message, help_message, parse_mode='Markdown')
                
    def take_snapshoot(self, message):
        if str(message.chat.id) in TELEGRAM_CHAT_IDS:
            response = requests.get(f'{CAM_IP_URI}/cgi-bin/snapshot.sh?res=high&watermark=yes')
            if response.status_code == 200:
                self.bot.send_photo(message.chat.id, photo=response.content)
            else:
                LOGGER.error(f"Error al enviar el snapshoot. Código de estado: {response.status_code}")
                
    def moveCam(self, message):
        if str(message.chat.id) in TELEGRAM_CHAT_IDS:
            response = requests.get(f'{CAM_IP_URI}/cgi-bin/get_configs.sh?conf=ptz_presets')
            
            if response.status_code == 200:
                response_json = response.json()
                markup = telebot.types.InlineKeyboardMarkup()
                
                for key, value in response_json.items():
                    values = value.split(',')
                    if values[0] and values[0] != 'NULL':
                        option = telebot.types.InlineKeyboardButton(values[0].capitalize(), callback_data=key)
                        markup.add(option)
                
                self.bot.send_message(message.chat.id, "Apuntar camara a:", reply_markup=markup)

            else:
                LOGGER.error(f"Error recuperando los presets. Código de estado: {response.status_code}")

    def status(self, message):
        if str(message.chat.id) in TELEGRAM_CHAT_IDS:
            response = requests.get(f'{CAM_IP_URI}/cgi-bin/get_configs.sh?conf=camera')

            if response.status_code == 200:
                response_json = response.json()

                self.bot.send_message(
                    message.chat.id, 
                    f"Status:\n\nSWITCH_ON: {response_json['SWITCH_ON']}\nMOTION DETECTION: {response_json['MOTION_DETECTION']}\n"
                )


            #http://192.168.1.129/cgi-bin/camera_settings.sh?motion_detection=yes
            #http://192.168.1.129/cgi-bin/getlastrecordedvideo.sh?type=4
            
    def callback_query(self, call):
        response = requests.get(f'{CAM_IP_URI}/cgi-bin/preset.sh?num={call.data}&action=go_preset')
        if response.status_code == 200:
            LOGGER.info(f"Camara apuntando a preset {call.data}")
            self.bot.answer_callback_query(call.id, "Moviendo la camara...")
        else:
            LOGGER.error(f"Error al mover la camara. Código de estado: {response.status_code}")
            
