import paho.mqtt.client as mqtt
import numpy as np
import random, requests, cv2, yaml
from datetime import datetime
from config import *
import onnxruntime as ort

class PersonDetector:

    def __init__(self):
        self.session = ort.InferenceSession('/yicam-processor/service/yolov8s.onnx', providers=["CPUExecutionProvider"])
        self.confidence_thres = 0.5
        self.iou_thres = 0.5
        self.classes = self.load_classes_from_yaml('https://raw.githubusercontent.com/ultralytics/ultralytics/refs/heads/main/ultralytics/cfg/datasets/coco8.yaml')
        self.color_palette = np.random.uniform(0, 255, size=(len(self.classes), 3))
        

    def load_classes_from_yaml(self, yaml_url):
        response = requests.get(yaml_url)
        if response.status_code == 200:
            yaml_content = yaml.safe_load(response.text) 
            return yaml_content.get("names", []) 
        else:
            print(f"Error al descargar el YAML: {response.status_code}")
            return []

    def detect_person(self, client, userdata, message):
        try:
            now = datetime.now()
            formatted_time = now.strftime("%H:%M:%S %d/%m/%Y")
            print(f"Evento de movimiento recibido: {formatted_time}", flush=True)

            image_data = np.frombuffer(message.payload, dtype=np.uint8)
            self.input_image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
            
             # Get the model inputs
            model_inputs = self.session.get_inputs()

            # Store the shape of the input for later use
            input_shape = model_inputs[0].shape
            self.input_width = input_shape[2]
            self.input_height = input_shape[3]

            img_data = self.preprocess()

            outputs = self.session.run(None, {model_inputs[0].name: img_data})

            self.postprocess(self.input_image, outputs)

        except Exception as e:
            print(f"Error procesando la imagen: {e}", flush=True)
            

    # Función para enviar la imagen a Telegram
    def send_telegram_alert(self, image_path):
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
    def setup_mqtt(self):
        client_id = f'python-mqtt-{random.randint(0, 1000)}'
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)

        client.on_message = self.detect_person
        client.connect(MQTT_SERVER, 1883, 60) 
        client.subscribe(MQTT_MOTION_TOPIC)

        # Iniciar el loop del cliente 
        print(f"MQTT client: {client_id}", flush=True)
        print("Service started. Listening for messages...", flush=True)
        client.loop_forever()

    def main(self):
        self.setup_mqtt()

    def preprocess(self):
        """
        Preprocesses the input image before performing inference.

        Returns:
            image_data: Preprocessed image data ready for inference.
        """

        # Get the height and width of the input image
        self.img_height, self.img_width = self.input_image.shape[:2]

        # Convert the image color space from BGR to RGB
        img = cv2.cvtColor(self.input_image, cv2.COLOR_BGR2RGB)

        # Resize the image to match the input shape
        img = cv2.resize(img, (self.input_width, self.input_height))

        # Normalize the image data by dividing it by 255.0
        image_data = np.array(img) / 255.0

        # Transpose the image to have the channel dimension as the first dimension
        image_data = np.transpose(image_data, (2, 0, 1))  # Channel first

        # Expand the dimensions of the image data to match the expected input shape
        image_data = np.expand_dims(image_data, axis=0).astype(np.float32)

        # Return the preprocessed image data
        return image_data

    def postprocess(self, input_image, output):
        """
        Performs post-processing on the model's output to extract bounding boxes, scores, and class IDs.

        Args:
            input_image (numpy.ndarray): The input image.
            output (numpy.ndarray): The output of the model.

        Returns:
            numpy.ndarray: The input image with detections drawn on it.
        """
        # Transpose and squeeze the output to match the expected shape
        outputs = np.transpose(np.squeeze(output[0]))

        # Get the number of rows in the outputs array
        rows = outputs.shape[0]

        # Lists to store the bounding boxes, scores, and class IDs of the detections
        boxes = []
        scores = []
        class_ids = []

        # Calculate the scaling factors for the bounding box coordinates
        x_factor = self.img_width / self.input_width
        y_factor = self.img_height / self.input_height

        # Iterate over each row in the outputs array
        for i in range(rows):
            # Extract the class scores from the current row
            classes_scores = outputs[i][4:]

            # Find the maximum score among the class scores
            max_score = np.amax(classes_scores)

            # If the maximum score is above the confidence threshold
            if max_score >= self.confidence_thres:
                # Get the class ID with the highest score
                class_id = np.argmax(classes_scores)

                # Extract the bounding box coordinates from the current row
                x, y, w, h = outputs[i][0], outputs[i][1], outputs[i][2], outputs[i][3]

                # Calculate the scaled coordinates of the bounding box
                left = int((x - w / 2) * x_factor)
                top = int((y - h / 2) * y_factor)
                width = int(w * x_factor)
                height = int(h * y_factor)

                # Add the class ID, score, and box coordinates to the respective lists
                class_ids.append(class_id)
                scores.append(max_score)
                boxes.append([left, top, width, height])

        # Apply non-maximum suppression to filter out overlapping bounding boxes
        indices = cv2.dnn.NMSBoxes(boxes, scores, self.confidence_thres, self.iou_thres)

        person_detected = False
        # Iterate over the selected indices after non-maximum suppression
        for i in indices:
            # Get the box, score, and class ID corresponding to the index
            box = boxes[i]
            score = scores[i]
            class_id = class_ids[i]

            # Draw the detection on the input image
            self.draw_detections(input_image, box, score, class_id)

            if class_id == 0:
                person_detected = True

        if person_detected:
            output_path = "output_detected_image.jpg"
            cv2.imwrite(output_path, input_image)
            self.send_telegram_alert(output_path)
        else:
            print("No se detectó ninguna persona.", flush=True)

    def draw_detections(self, img, box, score, class_id):
        """
        Draws bounding boxes and labels on the input image based on the detected objects.

        Args:
            img: The input image to draw detections on.
            box: Detected bounding box.
            score: Corresponding detection score.
            class_id: Class ID for the detected object.

        Returns:
            None
        """
        # Extract the coordinates of the bounding box
        x1, y1, w, h = box

        # Retrieve the color for the class ID
        color = self.color_palette[class_id]

        # Draw the bounding box on the image
        cv2.rectangle(img, (int(x1), int(y1)), (int(x1 + w), int(y1 + h)), color, 2)

        # Create the label text with class name and score
        label = f"{self.classes[class_id]}: {score:.2f}"

        # Calculate the dimensions of the label text
        (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

        # Calculate the position of the label text
        label_x = x1
        label_y = y1 - 10 if y1 - 10 > label_height else y1 + 10

        # Draw a filled rectangle as the background for the label text
        cv2.rectangle(
            img, (label_x, label_y - label_height), (label_x + label_width, label_y + label_height), color, cv2.FILLED
        )

        # Draw the label text on the image
        cv2.putText(img, label, (label_x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

if __name__ == "__main__":
    detection = PersonDetector()
    detection.main()