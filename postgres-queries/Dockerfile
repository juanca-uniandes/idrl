FROM python:3.9

WORKDIR /app

# Copiar los archivos de la aplicación y el archivo de requisitos
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

# Copiar wait-for-it.sh al directorio /app
COPY wait-for-it.sh .

# Cambiar permisos para wait-for-it.sh
RUN chmod +x wait-for-it.sh

# Ejecutar wait-for-it.sh antes de iniciar la aplicación
CMD ["./wait-for-it.sh", "postgres:5432", "--", "python", "app.py"]
