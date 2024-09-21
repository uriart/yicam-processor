import paho.mqtt.client as mqtt
import numpy as np
import random, requests, telebot, cv2
from datetime import datetime
from config import *
from ultralytics import YOLO

model = YOLO('yolov8s.pt')

def detect_person(image):
    """Detecta personas en una imagen utilizando YOLOv5."""

    results = model(image)
    detections = results[0]

    # Revisar si se detectó una persona
    person_detected = False
    for detection in detections.boxes.data.tolist():
        class_id = int(detection[5])
        if class_id == 0:  # Clase '0' en COCO es 'person'
            person_detected = True
            # Dibujar el rectángulo alrededor de la persona detectada
            x1, y1, x2, y2 = map(int, detection[:4])
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Guardar la imagen con las detecciones en disco
    output_path = "output_detected_image.jpg"
    cv2.imwrite(output_path, image)

    now = datetime.now()
    formatted_time = now.strftime("%H:%M:%S %d/%m/%Y")
    print(f"Evento de movimiento recibido: {formatted_time}", flush=True)

    if person_detected:
        send_telegram_alert(output_path)
    else:
        print("No se detectó ninguna persona.", flush=True)

def on_message(client, userdata, message):
    try:
        image_data = np.frombuffer(message.payload, dtype=np.uint8)
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
        detect_person(image)

    except Exception as e:
        print(f"Error procesando la imagen: {e}", flush=True)

# Función para enviar la imagen a Telegram
def send_telegram_alert(image_path):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto'
    for chat_id in TELEGRAM_CHAT_ID:
        with open(image_path, 'rb') as image:
            files = {'photo': image}
            data = {'chat_id': chat_id, 'caption': '🚨 Persona detectada.'}
            response = requests.post(url, files=files, data=data)
            if response.status_code == 200:
                print("Alerta de detección de persona enviada a Telegram.", flush=True)
            else:
                print(f"Error al enviar la alerta. Código de estado: {response.status_code}", flush=True)

# Configurar el cliente MQTT
def setup_mqtt():
    client_id = f'python-mqtt-{random.randint(0, 1000)}'
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)

    client.on_message = on_message
    client.connect(MQTT_SERVER, 1883, 60) 
    client.subscribe(MQTT_MOTION_TOPIC)

    # Iniciar el loop del cliente 
    print(f"MQTT client: {client_id}", flush=True)
    print("Service started. Listening for messages...", flush=True)
    client.loop_forever()

def main():
    setup_mqtt()

if __name__ == "__main__":
    main()
