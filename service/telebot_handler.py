import telebot
from config import *
from logging_utils import LOGGER
import requests

class TelebotHandler:

    def __init__(self):
        self.bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
        self.bot.message_handler(commands=['help'], )(self.help)

        self.bot.message_handler(commands=['snapshoot'], )(self.take_snapshoot)

    def run(self):
        LOGGER.info("Telebot handler started.")
        self.bot.infinity_polling()

    def help(self, message):
        if str(message.chat.id) in TELEGRAM_CHAT_IDS:
                help_message = (
                    "🌟 **Ayuda del Bot** 🌟\n\n"
                    "¡Hola! Aquí tienes una lista de comandos que puedes usar:\n\n"
                    "1️⃣ **/help** - Muestra este mensaje de ayuda.\n"
                    "2️⃣ **/snapshot** - Toma una instantánea de la cámara IP y la envía aquí.\n\n"
                    "Si tienes alguna pregunta adicional, no dudes en preguntar. ¡Estoy aquí para ayudarte! 😊"
                )
                self.bot.reply_to(message, help_message, parse_mode='Markdown')
                
    def take_snapshoot(self, message):
        if str(message.chat.id) in TELEGRAM_CHAT_IDS:
            response = requests.get(f'{CAM_IP_URI}/cgi-bin/snapshot.sh?res=high&watermark=yes')
            if response.status_code == 200:
                self.bot.send_photo(message.chat.id, photo=response.content)
            else:
                LOGGER.error(f"Error al enviar el snapshoot. Código de estado: {response.status_code}")
            
