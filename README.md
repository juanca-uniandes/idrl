### Pasos para el despliegue del proyecto

- **Instalación de Docker:**
  - Asegúrate de tener Docker instalado en tu sistema. Puedes descargar e instalar Docker desde [este enlace](https://docs.docker.com/get-docker/). Se recomienda utilizar la versión Docker 25.0.3 o superior.

- **Clonar el repositorio:**
  - Clona el repositorio del proyecto desde GitHub ejecutando el siguiente comando en tu terminal:
    ```bash
    git clone https://github.com/juanca-uniandes/idrl.git
    ```

- **Iniciar los contenedores Docker:**
  - Navega al directorio del proyecto clonado:
    ```bash
    cd idrl
    ```
  - Ejecuta el siguiente comando para iniciar los contenedores Docker definidos en el archivo `docker-compose.yml`:
    ```bash
    docker-compose up
    ```

- **Verificar el despliegue:**
  - Todos los endpoints que se van a mostrar a continuación deben llevar como header el content type application/json:
    1. **Registro de usuario:**
       - Para registrar el usuario, realiza una solicitud POST a `http://127.0.0.1:5050/register` con un body que contenga el username, email y password como información **[Todos estos campos son requeridos y username y email deberán ser únicos]**. Ejemplo:
         ```json
         {
             "username": "admin",
             "email": "admin@gmail.com",
             "password": "admin"
         }
         ```
    2. **Solicitud del token para poder hacer peticiones a los demás end-points:**
       - Para solicitar el token, realiza una solicitud POST a `http://127.0.0.1:5050/login` con un body que contenga el email y el password. Ejemplo:
         ```json
         {
             "email": "admin@gmail.com",
             "password": "12345"
         }
         ```
       - Una vez realizada la solicitud y si las credenciales son correctas, se obtendrá la siguiente respuesta similar a esta:
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
    3. **Cargar video para ser procesado:**
       - Para hacer la solicitud de la carga del video, realiza una solicitud POST a `http://127.0.0.1:5004/task/start` con Autorización Bearer, donde el valor de dicha autorización es el token generado en el paso 2. Además, en el body se deberá enviar el siguiente cuerpo que contiene un parámetro `url`, donde dicha url es la url de donde se obtendrá el video. Los formatos distintos a los permitidos (MP4) serán descartados. Ejemplo de cómo debería lucir la solicitud:
         ```bash
         curl --location 'http://localhost:5004/task/start' \
         --header 'Content-Type: application/json' \
         --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw' \
         --data  '{
             "url": "https://cdn.pixabay.com/video/2023/06/28/169249-840702546_large.mp4"
         }'
         ```
       - Ejemplo del body de la solicitud:
         ```json
         {
             "url": "https://cdn.pixabay.com/video/2023/06/28/169249-840702546_large.mp4"
         }
         ```
