### Arquitectura
Se ha desplegado en GCP una de base de datos y 3 maquinas virtuales en GCP las cuales se encuentran en el mismo segmento de red. En cada instancia se han desplegado los contenedores previamente desarrollados de modo que funcionen de manera independiente en cada maquina virtual.
![arquitectura](https://github.com/juanca-uniandes/idrl/assets/142269475/0e82739a-8f82-47a1-b301-47dcbaa1d8bd)

La distribucion de los componentes se detalla a continuacion:

- **Web-Server:**
    - Contenedor Nginx: Configurado como un proxy, para atender las peticiones del usuario,
    - Autorization: Su labor principal es autenticar al usuario con el proposito de proteger a los endpoins que deban estar autorizados.
- **Worker-Server:**
    - Worker: Lleva a cabo la tarea mas "pesada" del sistema, el procesamiento de videos
    - Tasks: Se ocupa de tareas mas livianas, llevadas a cabo de manera sincrona, por ejemplo consultar el estado de una tarea.
    - Redis: Cola de mensajes para llevar a cado las tareas asincronas.
- **File Server:**
Se encarga de almacenar los videos descargados y procesados

- **Cloud SQL:**
Instancia de base de datos en Postgres

### Tecnologías asociadas
- Docker
- Flask
- Redis
- Celery
- PostgreSQL
- JMeter

### Almacenamiento de archivos:
- En el File Server se ha compartido el folder "/var/nfs/shared_folder"
- Los contenedores que desean escribir en ese folder compartido deben mapear un volumen hacia el folder "/usr/remote_folder" del sistema de archivos de maquina anfitriona
- El folder "/usr/remote_folder" de la maquina "worker-server", se ha configurado previamente para mapear el contenido compartido en "/var/nfs/shared_folder" del "File Server".
![file_server](https://github.com/juanca-uniandes/idrl/assets/142269475/63a1c7c8-1dcb-4a92-b710-a1e070d21303)

### Pasos para el despliegue del proyecto en Ambiente Cloud GCP

- **GCP**
En GCP debemos generar un proyecto y seleccionarlo, seguido a eso entramos a *Compute Engine* donde creamos una Instancia de VM con las caracteristicas solicitadas 2 vCPU, 2 GiB en RAM y 20 GiB en almacenamiento, para esta prueba les instalamos un sistema ubuntu a las maquinas, una maquina para cada instancia requerida. Para este caso requerimos 3 instancias una para el `web-server`, `worker-server` y `file-storage`.

Una ves creada las instancias accedemos a ellas por *SSH* e iniciamos el proceso de configuracion de las instancias para cual debemos realiza una serie de instalaciones a nuestas intancias de VM con sistema ubuntu:

    - **Instalación de Docker:**
      - Para este requerimos instalar docker en ubuntu, para realizar esta instalacion puede seguir este tutorial "https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04-es"

    - **Instalación de Python:**
      - Para realizar esta instalacion puede seguir este tutorial "https://www.hostinger.co/tutoriales/instalar-python-pip-ubuntu"

    - **Instalación de Git:**
      - Para realizar esta instalacion puede seguir este tutorial "https://simplecodetips.wordpress.com/2018/06/08/instalar-y-conectar-git-con-github-mediante-ssh/"

    - **Instalación de Nano:**
      -  Para realizar esta instalacion puede seguir este tutorial "https://www.hostinger.co/tutoriales/instalar-nano-text-editor"

- **Clonar el repositorio:**
  - Clona el repositorio del proyecto desde GitHub ejecutando el siguiente comando en tu terminal:
    ```bash
    git clone https://github.com/juanca-uniandes/idrl.git
    ```

  * Para el caso del despliegue en la nueve de gcp se debe entrar al codigo y modificar las rutas. Para esto validamos las IP asignadas po GCP para las instancias de VM.
![Screenshot_10](https://github.com/juanca-uniandes/idrl/assets/142316997/a83fa2c5-a498-4938-9fa4-5db2d9a1fc10)

  Y devemos entrar a modifcar con nano los archivos `web-server/app/app.py` validando la IP privada del worker-server `TASKS_URL = 'http://<IP_worker_server>:5004/tasks'`, `worker-server/app/tasks.py`, `worker-server/app/utils.py`  validando la IP privada del file-server `URL_ALMACENAR = "http://<URL_FILE_SERVER>:5001"`, adicional en `web-server/app/.env`, `worker-server/app/.env`  validamos y cambiamos los datos del host de la base de datos`POSTGRES_HOST="<URL_DB>"` y el puerto que utiliza la base de datos `POSTGRES_PORT="<PORT_DB>"` antes de realizar los despliegues de las maquinas virtuales.


- **Iniciar los contenedores Docker:**
    - **web-server**
      - Una vez clonado el repositorio, navega al directorio del proyecto clonado:
        ```bash
        cd idrl
        ```

        ```bash
        cd web-server
        ```

  - Inicia los contenedores Docker definidos en el archivo `docker-compose.yml` contenido en las carpetas web-server y psg  ejecutando el siguiente comando:
    ```bash
    docker-compose up
    ```
    
    - **worker-server**
  - Para el worker-server es necesaria realizar una modificación dentro del archivo `worker-server/docker-compose.yml` se deben editar las networks, cambiando el parametro `- web-server_network`  por ` - network `  y el parametro `external: true`  por `driver: bridge` y despues si levantar el servidor worker-server ejecutando el siguiente comando:
  
        ```bash
        cd idrl
        ```

        ```bash
        cd web-server
        ```
    - Inicia los contenedores Docker definidos en el archivo `docker-compose.yml` contenido en las carpetas web-server y psg  ejecutando el siguiente comando:
      ```bash
      docker-compose up
      ```


      - **Cloud SQL
  - Consideraciones: Si el sistema operativo es Windows, debes reemplazar la línea `CMD ["./wait-for-it.sh", "postgres:5432", "--", "python", "app.py"]` por `CMD ["python", "app.py"]`, y comentar la linea `RUN chmod +x wait-for-it.sh`  en el archivo `postgres-queries/Dockerfile`, adicional tambien debes comentar la linea `command: ["./wait-for-it.sh", "postgres:5432", "--", "python", "app.py"]` en el archivo `docker-compose.yml`. Luego, ejecuta nuevamente el contenedor `postgres-queries` después de que `docker-compose up` haya finalizado todo el despliegue. Esta consideración no es necesaria en sistemas operativos como Ubuntu y macOS.
  - Para que la el web-server y el worker-server enlacen con la base de datos local, se debe entrar a los archivos `.env` ubicados en las carpetas `web-server`,`worker-server`, remplazar el host por `postgres` y el port por `5432`


    

### [Collection Postman](https://github.com/juanca-uniandes/idrl/blob/main/CLOUD%20VIDEOS%20MGMT.postman_collection.json)
  - **Verificar el despliegue:**
  - Todos los endpoints que se detallan a continuación requieren el encabezado `Content-Type: application/json`:

    1. **Registro de usuario:**
      - Realiza una solicitud POST a `http://<IP_PUBLICA_WEB_SERVER>:5050/auth/signup` con un cuerpo que contenga los siguientes campos:
      ```json
      {
          "username": "admin",
          "email": "admin@gmail.com",
          "password": "Admin123",
          "password_2": "Admin123"
      }
      ```

    2. **Obtener token de acceso:**
      - Realiza una solicitud POST a `http://<IP_PUBLICA_WEB_SERVER>:5050/auth/login` con un cuerpo que contenga el email y la contraseña del usuario. Ejemplo:
      ```json
      {
          "email": "admin@gmail.com",
          "password": "Admin123",
      }
      ```
      - Si las credenciales son correctas, recibirás una respuesta similar a esta:
      ```json
      {
          "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMzI3OTF9.NYZMPhV1pXbksebkOs-ORUpub737iJYo_8kToAWb8so"
      }
      ```

    3. **Cargar video para procesamiento:**
      - Realiza una solicitud POST a `http://<IP_PUBLICA_WEB_SERVER>:5050/tasks` con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso anterior. En el cuerpo de la solicitud, proporciona la URL del video que se va a procesar. Por ejemplo:
      ```bash
      curl --location 'http://<IP_PUBLICA_WEB_SERVER>:5050/tasks' \
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
      4. **Consultar estado de todas las tareas**
      - Realiza una solicitud GET a http://<IP_PUBLICA_WEB_SERVER>:5050/tasks?max=4&order=1 con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - El parametro "max" indica el numero maximo de registros
      - El parametro "order" especifica el orden en que se muestran los datos, 0 si es ascendete y 1 si es descendente
      - Ejemplo:
    ```
    curl --location 'http://<IP_PUBLICA_WEB_SERVER>:5050/tasks?max=4&order=1' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```
    5. **Consultar estado de una tarea**
      - Realiza una solicitud GET a http://<IP_PUBLICA_WEB_SERVER>:5050/tasks/<ID_TASK> con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - ID-TASK es el codigo de la tarea 
      - Ejemplo:
    ```
    curl --location 'http://<IP_PUBLICA_WEB_SERVER>:5050/tasks/bf5ae39c-751a-439f-9a03-88a19e20c360' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```
  
    6. **Abortar una tarea:**
      - Realiza una solicitud DELETE a http://<IP_PUBLICA_WEB_SERVER>:5050/tasks/<ID_TASK> con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - ID-TASK es el codigo de la tarea, que se puede obtener de la consulta especificada en el paso (4)
      - Ejemplo:
    ```
    curl -X DELETE --location 'http://<IP_PUBLICA_WEB_SERVER>:5050/tasks//bf5ae39c-751a-439f-9a03-88a19e20c360' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```



### Pasos para el despliegue del proyecto en Ambiente local

- **Instalación de Docker:**
  - Asegúrate de tener Docker instalado en tu sistema. Puedes descargar e instalar Docker desde [este enlace](https://docs.docker.com/get-docker/). Se recomienda utilizar la versión Docker 25.0.3 o superior.

- **Clonar el repositorio:**
  - Clona el repositorio del proyecto desde GitHub ejecutando el siguiente comando en tu terminal:
    ```bash
    git clone https://github.com/juanca-uniandes/idrl.git
    ```

- **Iniciar los contenedores Docker:**
  Para este caso se debe desplegar primero el servidor web-server y posterior a este se  pueden desplegar los demas.

  - Una vez clonado el repositorio, navega al directorio del proyecto clonado:
    ```bash
    cd idrl
    ```
    ```bash
    cd <CARPETA_SERVIDOR_A_DESPLEGAR>
    ```
  - Inicia los contenedores Docker definidos en el archivo `docker-compose.yml` contenido en las carpetas web-server y psg  ejecutando el siguiente comando:
    ```bash
    docker-compose up
    ```
  - Para el worker-server es necesaria realizar una modificación dentro del archivo `worker-server/docker-compose.yml` se deben editar las networks, cambiando el parametro ` - network ` por `- web-server_network`  y el parametro `driver: bridge` por `external: true` y despues si levantar el servidor worker-server ejecutando el siguiente comando:
    ```bash
    docker-compose up
    ```
  - Consideraciones: Si el sistema operativo es Windows, debes reemplazar la línea `CMD ["./wait-for-it.sh", "postgres:5432", "--", "python", "app.py"]` por `CMD ["python", "app.py"]`, y comentar la linea `RUN chmod +x wait-for-it.sh`  en el archivo `postgres-queries/Dockerfile`, adicional tambien debes comentar la linea `command: ["./wait-for-it.sh", "postgres:5432", "--", "python", "app.py"]` en el archivo `docker-compose.yml`. Luego, ejecuta nuevamente el contenedor `postgres-queries` después de que `docker-compose up` haya finalizado todo el despliegue. Esta consideración no es necesaria en sistemas operativos como Ubuntu y macOS.
  - Para que la el web-server y el worker-server enlacen con la base de datos local, se debe entrar a los archivos `.env` ubicados en las carpetas `web-server`,`worker-server`, remplazar el host por `postgres` y el port por `5432`

- **Verificar el despliegue:**
  - Todos los endpoints que se detallan a continuación requieren el encabezado `Content-Type: application/json`:

    1. **Registro de usuario:**
      - Realiza una solicitud POST a `http://127.0.0.1:5050/auth/signup` con un cuerpo que contenga los siguientes campos:
      ```json
      {
          "username": "admin",
          "email": "admin@gmail.com",
          "password": "Admin123",
          "password_2": "Admin123"
      }
      ```

    2. **Obtener token de acceso:**
      - Realiza una solicitud POST a `http://127.0.0.1:5050/auth/login` con un cuerpo que contenga el email y la contraseña del usuario. Ejemplo:
      ```json
      {
          "email": "admin@gmail.com",
          "password": "Admin123",
      }
      ```
      - Si las credenciales son correctas, recibirás una respuesta similar a esta:
      ```json
      {
          "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMzI3OTF9.NYZMPhV1pXbksebkOs-ORUpub737iJYo_8kToAWb8so"
      }
      ```

    3. **Cargar video para procesamiento:**
      - Realiza una solicitud POST a `http://127.0.0.1:5050/tasks` con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso anterior. En el cuerpo de la solicitud, proporciona la URL del video que se va a procesar. Por ejemplo:
      ```bash
      curl --location 'http://localhost:5050/tasks' \
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
      4. **Consultar estado de todas las tareas**
      - Realiza una solicitud GET a http://localhost:5050/tasks?max=4&order=1 con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - El parametro "max" indica el numero maximo de registros
      - El parametro "order" especifica el orden en que se muestran los datos, 0 si es ascendete y 1 si es descendente
      - Ejemplo:
    ```
    curl --location 'http://localhost:5050/tasks?max=4&order=1' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```
    5. **Consultar estado de una tarea**
      - Realiza una solicitud GET a http://localhost:5050/tasks/<ID_TASK> con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - ID-TASK es el codigo de la tarea 
      - Ejemplo:
    ```
    curl --location 'http://localhost:5050/tasks/bf5ae39c-751a-439f-9a03-88a19e20c360' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```
  
    6. **Abortar una tarea:**
      - Realiza una solicitud DELETE a http://127.0.0.1:5050/tasks/<ID_TASK> con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - ID-TASK es el codigo de la tarea, que se puede obtener de la consulta especificada en el paso (4)
      - Ejemplo:
    ```
    curl -X DELETE --location 'http://localhost:5050/tasks//bf5ae39c-751a-439f-9a03-88a19e20c360' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```

# Monitoreo a través de políticas

## Autoscaler - Utilización actual del Autoscaler por encima del 75% en 5 minutos

- **Nombre de la condición:** Autoscaler - Utilización actual del Autoscaler
- **Descripción:** Esta política monitorea la utilización actual del escalador automático. La alerta se activa si la utilización actual supera el umbral del 75% durante un período de 5 minutos. Esto indica que la carga de trabajo actual está utilizando más recursos de los que se considera óptimo.
- **Métrica:** Utiliza la métrica de utilización actual del escalador automático.
- **Umbral:** 75%
- **Conclusión:** Esta política se enfoca en el uso actual del escalador automático y activa la alerta si se detecta un uso excesivo de recursos durante un tiempo prolongado.

## Autoscaler - Capacidad de servicio por encima del 75% en 5 minutos

- **Nombre de la condición:** Autoscaler - Capacidad de servicio
- **Descripción:** Esta política monitorea la capacidad de servicio del sistema. La alerta se activa si la capacidad de servicio supera el 75% durante un período de 5 minutos. Esto indica que la capacidad del sistema está siendo sobrepasada por la carga de trabajo actual.
- **Métrica:** Utiliza la métrica de capacidad de servicio del sistema.
- **Umbral:** 75%
- **Conclusión:** Esta política se enfoca en la capacidad de servicio del sistema y activa la alerta si se detecta que la carga de trabajo actual está superando la capacidad máxima que el sistema puede manejar eficientemente durante un período de tiempo prolongado.

## Autoscaler - Capacidad de servicio cuando no hay datos durante un periodo específico

- **Nombre de la condición:** Autoscaler - Capacidad de servicio
- **Descripción:** Esta política monitorea la capacidad de servicio del sistema. La alerta se activa si no se reciben datos para la métrica durante un período de 1 hora. Esto puede indicar un problema con la recolección de datos o una falta de comunicación entre los componentes del sistema.
- **Métrica:** Utiliza la métrica "autoscaler.googleapis.com/capacity", que proporciona información sobre la capacidad de servicio del sistema.
- **Tipo de Condición:** Ausencia de Métrica (Metric absence)
- **Activador de la Alerta:** La alerta se activa si no se reciben datos para la métrica durante un período de 1 hora.
- **Conclusión:** Esta política permite monitorear la capacidad de servicio del sistema y recibir notificaciones si no se reciben datos durante un período de 1 hora, lo que puede indicar un problema en la recolección de datos o en la comunicación entre los componentes del sistema.

## Grupo de Instancias - Tamaño del grupo por encima de 4 instancias en 1 hora

- **Descripción:** Esta política de alerta monitorea el tamaño del grupo de instancias en Google Cloud Platform (GCP), notificando si el número de máquinas virtuales (VMs) en el grupo excede 4 instancias en cualquier momento dentro de un período de 1 hora.
- **Métrica:** Utiliza la métrica compute.googleapis.com/instance_group/size, que proporciona información sobre el tamaño del grupo de instancias.
- **Tipo de Recurso:** Está asociada con el recurso instance_group, lo que significa que se aplica a los grupos de instancias en GCP.
- **Umbral:** El umbral está configurado en 4 instancias.
- **Conclusión:** Esta política permite monitorear el tamaño del grupo de instancias en Google Cloud Platform (GCP). Si en cualquier momento dentro de un período de 1 hora hay 4 o más instancias en el grupo, se activará la alerta.

## Autoscaler - Utilización actual del Autoscaler por encima del 90% en 30 minutos

- **Nombre de la condición:** Autoscaler - Utilización actual del Autoscaler
- **Descripción:** Esta política monitorea la utilización actual del escalador automático. La alerta se activa si la utilización actual supera el umbral del 90% durante un período de 30 minutos. Esto indica que la carga de trabajo actual está utilizando más recursos de los que se considera óptimo y está llegando a su límite.
- **Métrica:** Utiliza la métrica de utilización actual del escalador automático.
- **Umbral:** 90%
- **Conclusión:** Esta política se enfoca en el uso actual del escalador automático y activa la alerta si se detecta excesivo de recursos durante un tiempo prolongado (30 minutos), lo que indicaría una posible necesidad de ajuste en la configuración de escalado para garantizar un rendimiento óptimo del sistema.

## Monitoreo a través de gráficos

- Gráfico de Capacidad de servicio
- Gráfico de Utilización actual del Autoscaler
- Gráfico de Tamaño del grupo de instancias
  ![image](https://github.com/juanca-uniandes/idrl/assets/142238841/92a74e11-9762-4217-b6bb-b3f1b8b0ca74)

## Verificaciones de tiempo de actividad

- **Verificación de la salud de los servidores en el balanceador de carga en la nube**
  - **Protocolo:** HTTP
  - **Tipo de recurso:** URL
  - **Hostname:** 34.36.153.134
  - **Frecuencia de la verificación:** 1 minuto
  - **Tiempo de espera de respuesta:** 10 segundos
  - **Registrar fallos de verificación:** Verdadero
  - **Código de respuesta HTTP aceptable:** 2XX
- **Conclusión:** La implementación de una alerta de verificación de latencia con la configuración detallada proporciona un monitoreo casi en tiempo real de la disponibilidad de los servidores. Esto permite una detección temprana de problemas, una respuesta oportuna y, en última instancia, mejora la confiabilidad del sistema al garantizar que los servidores respondan correctamente.

