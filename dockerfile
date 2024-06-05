FROM python:3.12

RUN git clone https://github.com/JCMSimon/ValorVodAuto /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "running.py"]