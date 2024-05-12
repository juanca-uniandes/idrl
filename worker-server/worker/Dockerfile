FROM python:3.12

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .


RUN mkdir -p /app/videos/processed
RUN mkdir -p /app/videos/uploads

CMD ["python", "app.py"]
