FROM python:3.9.20

RUN apt-get update && apt-get install -y libgl1-mesa-glx

COPY . /yicam-processor
WORKDIR /yicam-processor

RUN pip install -r requirements.txt

CMD ["python", "service/main.py"]