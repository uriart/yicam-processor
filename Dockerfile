FROM python:3.9.20

RUN apt-get update && apt-get install -y libgl1-mesa-glx

COPY . /yicam-processing
WORKDIR /yicam-processing

RUN pip install -r requirements.txt

CMD ["python", "service/main.py"]