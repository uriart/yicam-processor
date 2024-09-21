FROM python:3.9.20

RUN apt-get update && apt-get install -y libgl1-mesa-glx

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY . /yicam-processor
WORKDIR /yicam-processor

CMD ["python", "service/main.py"]