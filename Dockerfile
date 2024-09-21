FROM python:3.9.20-slim

COPY requirements.txt /requirements.txt
RUN pip install -r requirements.txt

COPY . /yicam-processor
WORKDIR /yicam-processor

CMD ["python", "service/main.py"]