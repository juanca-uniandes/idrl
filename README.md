### Tecnologías asociadas
- Docker
- Flask
- Redis
- Celery
- PostgreSQL
- JMeter

### Pasos para el despliegue del proyecto

- **Instalación de Docker:**
  - Asegúrate de tener Docker instalado en tu sistema. Puedes descargar e instalar Docker desde [este enlace](https://docs.docker.com/get-docker/). Se recomienda utilizar la versión Docker 25.0.3 o superior.

- **Clonar el repositorio:**
  - Clona el repositorio del proyecto desde GitHub ejecutando el siguiente comando en tu terminal:
    ```bash
    git clone https://github.com/juanca-uniandes/idrl.git
    ```

- **Iniciar los contenedores Docker:**
  - Una vez clonado el repositorio, navega al directorio del proyecto clonado:
    ```bash
    cd idrl
    ```
  - Inicia los contenedores Docker definidos en el archivo `docker-compose.yml` ejecutando el siguiente comando:
    ```bash
    docker-compose up
    ```

  - Consideraciones: Si el sistema operativo es Windows, debes reemplazar la línea `CMD ["./wait-for-it.sh", "postgres:5432", "--", "python", "app.py"]` por `CMD ["python", "app.py"]` en el archivo `postgres-queries/Dockerfile`. Luego, ejecuta nuevamente el contenedor `postgres-queries` después de que `docker-compose up` haya finalizado todo el despliegue. Esta consideración no es necesaria en sistemas operativos como Ubuntu y macOS.

- **Verificar el despliegue:**
  - Todos los endpoints que se detallan a continuación requieren el encabezado `Content-Type: application/json`:

    1. **Registro de usuario:**
      - Realiza una solicitud POST a `http://127.0.0.1:5050/register` con un cuerpo que contenga los siguientes campos:
      ```json
      {
          "username": "admin",
          "email": "admin@gmail.com",
          "password": "admin"
      }
      ```

    2. **Obtener token de acceso:**
      - Realiza una solicitud POST a `http://127.0.0.1:5050/login` con un cuerpo que contenga el email y la contraseña del usuario. Ejemplo:
      ```json
      {
          "email": "admin@gmail.com",
          "password": "12345"
      }
      ```
      - Si las credenciales son correctas, recibirás una respuesta similar a esta:
      ```json
      {
          "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMzI3OTF9.NYZMPhV1pXbksebkOs-ORUpub737iJYo_8kToAWb8so",
          "user": {
              "email": "admin@gmail.com",
              "id": 1,
              "username": "admin"
          }
      }
      ```

    3. **Cargar video para procesamiento:**
      - Realiza una solicitud POST a `http://127.0.0.1:5050/task/start` con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso anterior. En el cuerpo de la solicitud, proporciona la URL del video que se va a procesar. Por ejemplo:
      ```bash
      curl --location 'http://localhost:5004/task/start' \
      --header 'Content-Type: application/json' \
      --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw' \
      --data  '{
          "url": "https://cdn.pixabay.com/video/2023/06/28/169249-840702546_large.mp4"
      }'
      ```
      - El cuerpo de la solicitud debe contener la URL del video a procesar:
      ```json
      {
          "url": "https://cdn.pixabay.com/video/2023/06/28/169249-840702546_large.mp4"
      }
      ```
