FROM python:3.11

RUN git clone https://github.com/JCMSimon/ValorVodAuto /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "main.py"]