# Utiliza una imagen base de Python
FROM python:3.12
WORKDIR /app
COPY requirements.txt requirements.txt
RUN mkdir -p /app/videos/processed
RUN mkdir -p /app/videos/uploads
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]