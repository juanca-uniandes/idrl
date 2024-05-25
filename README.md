# Arquitectura
Se ha desplegado en GCP una de base de datos, 2 servicios en Cloud Run, el PubSub y cloud storage. El primer servicio en Cloud Run esta construido a partir de una imagen de nuestro web server y el segundo servicio asociado a la imagen del worker.

![arquitectura-entrega-5](https://github.com/juanca-uniandes/idrl/assets/142269475/8c5c746c-6865-4d93-ad14-e544d1cf27da)

La distribucion de los componentes se detalla a continuacion:
- **Cloud Environment Web-Server:**
Esta construido a partir del contenedor "Web Server", incluye las funciones de autenticacion y los demas endpoints "sincronos" necesarios para implementar la solucion.
- **Cloud Environment Worker-Server:**
Esta construido a partir del contenedor "Worker", lleva a cabo la tarea mas "pesada" del sistema, el procesamiento de videos
- **Cloud SQL:**
Instancia de base de datos en Postgres
- **Cloud Storage::**
Se encarga de almacenar los videos descargados y procesados
- **PubSub:**
Utilizado para realizar la comunicacion asincrona entre los servicios "Web Server" y "Worker" implementados en Cloud Run, de esta manera las ambos servicios pueden escalar automaticamente de acuerdo a la carga de trabajo.
- **Monitoring:**
A travez de politicas monitorea los servicios implementados segun los parametros establecidos y de forma grafica.
- **Cloud Run:**
Despliega instancias para la ejecucion de procesos cortos, posee un balanceo de cargas y un escalador automatico. En Cloud Run se despliega el Web-Server y el Worker-Server.

# Tecnologías asociadas
- Docker
- Flask
- Cloud PudSub
- Cloud Run
- PostgreSQL
- JMeter

# Pasos para el despliegue del proyecto en Ambiente Cloud GCP
# Preparación del proyecto
-------------------------------------------------------------------------------
## 1. Nuevo proyecto
-------------------------------------------------------------------------------
Antes de comenzar con la configuración, asegúrate de tener un nuevo proyecto creado en Google Cloud Platform (GCP).

1. Habilitar el API de "Cloud Run".
2. Habilitar el API de "Pub Sub".
-------------------------------------------------------------------------------
## 2. VPC network -> Crear una regla de firewall
-------------------------------------------------------------------------------
Para permitir el tráfico entrante a tu instancia, necesitas configurar reglas de firewall.

1. Accede al menú "VPC network" y selecciona "Firewall".
2. Crea una nueva regla de firewall con los siguientes detalles:
   - Nombre: default-allow-http
   - Etiquetas del servidor: http-server
   - Rangos de direcciones IPv4 fuente: 0.0.0.0/0
   - Protocolos y puertos especificados: TCP / todos

-------------------------------------------------------------------------------
## 3. VPC network -> Crear una regla de firewall
-------------------------------------------------------------------------------
Además de la regla anterior, necesitarás otra para permitir el tráfico de comprobación de estado.

1. Accede al menú "VPC network" y selecciona "Firewall".
2. Crea una nueva regla de firewall con los siguientes detalles:
   - Nombre: default-allow-health-check
   - Etiquetas del servidor: http-server
   - Rangos de direcciones IPv4 fuente: 130.21.0.0/22, 35.191.0.0/16
   - Protocolos y puertos especificados: TCP / todos

-------------------------------------------------------------------------------
## 4. IAM Service account -> Crear un Rol y Cuenta de servicio con los permisos necesarios
-------------------------------------------------------------------------------
Es necesario utilizar una cuenta de servicio con los permisos necesarios para acceder a PubSub y Cloud Storage, en resumen la cuenta debe tener los siguientes permisos:
   - pubsub.subscriptions.consume
   - pubsub.subscriptions.create
   - pubsub.subscriptions.delete
   - pubsub.subscriptions.get
   - pubsub.subscriptions.list
   - pubsub.subscriptions.update
   - pubsub.topics.create
   - pubsub.topics.delete
   - pubsub.topics.detachSubscription
   - pubsub.topics.get
   - pubsub.topics.list
   - pubsub.topics.publish
   - pubsub.topics.update
   - pubsub.topics.updateTag
   - storage.buckets.create
   - storage.buckets.delete
   - storage.buckets.get
   - storage.buckets.list
   - storage.buckets.update
   - storage.objects.create
   - storage.objects.delete
   - storage.objects.get
   - storage.objects.list
   - storage.objects.update

-------------------------------------------------------------------------------
## 4. SQL -> Cloud Sql
-------------------------------------------------------------------------------
Crear una instancia de base de datos en PostgreSQL

-------------------------------------------------------------------------------
## 5. Cloud Run
-------------------------------------------------------------------------------

* Se debe colocar las credenciales en los archivos credentials-cuenta-storage.json del web-servee y el worker-server y se carga con la informacion del archivo [Credenciales-web-worker](Credenciales-Web-Worker.pdf)

#### a. Crear en Cloud Run, un servicio para el web server
1. Modificar el codigo previo ubicado en la carpeta "web-server"
2. Crear el servicio ubicandose en la carpeta `web-server` y ejecutando el siguiente comando:
 
```bash
 gcloud builds submit --tag gcr.io/web-server-420612/web-server
```
```bash
 gcloud run deploy web-server `
  --image gcr.io/web-server-420612/web-server `
  --platform managed `
  --region us-west1 `
  --allow-unauthenticated `
  --set-env-vars GOOGLE_CLOUD_PROJECT=web-server-420612 `
  --set-env-vars PUBSUB_TOPIC=post-task `
  --set-env-vars TASKS_URL=https://worker-server-65qdrdv3sq-uw.a.run.app
```

#### b. Crear en Cloud Run, un servicio para el worker
1. Modificar el codigo previo ubicado en la carpeta "worker-server"
2. Crear el servicio ubicandose en la carpeta `worker-server` y ejecutando el siguiente comando:

```bash
gcloud builds submit --tag gcr.io/web-server-420612/worker-server
```
```bash
gcloud run deploy worker-server `
 --image gcr.io/web-server-420612/worker-server `
 --platform managed `
 --region us-west1 `
 --allow-unauthenticated
```

-------------------------------------------------------------------------------
### 6. Cloud Storage - Create a Bucket
-------------------------------------------------------------------------------
#### a. Creacion
1. Accede al menú "Cloud Storage" y selecciona "bucket".
2. Crea un nuevo bucket con los siguientes detalles:
3. Haz clic en el botón "Crear bucket".
- Nombre: misoe3g23
- Almacenamiento: Multi-Region
- Clase de almacenamiento: Configura r una clase predeterminada - Standard
- Control de acceso: Prevención de acceso publico
- Control de acceso: Uniforme
- Proteger los datos: Ninguna
- Crear
- Prohibir acceso al publico: Aceptar

#### b. Asignacion de permisos
1. Una vez creado el bucket, selecciona el bucket recién creado.
2. Ve a la pestaña "Permisos".
3. Haz clic en el botón "Agregar miembro".
4. Ingresa el nombre de la cuenta de servicio asociada a tu instancia de Cloud Run.
5. Selecciona el rol apropiado para la cuenta de servicio (por ejemplo, "Storage Object Creator" o "Storage Object Admin").
6. Haz clic en el botón "Guardar".

-------------------------------------------------------------------------------
### 7. Pub Sub - Topic, Subscription
-------------------------------------------------------------------------------
Crear el "topic" y "subscription" de acuerdo a las siguientes características:

- Delivery type de tipo "Push"
- El endpoint asociado al punto anterior debe ser la URL del Cloud Run del worker-server
- Esta url debe soportar obligatoriamente el protocolo https

## Políticas de Alerta en Google Cloud Monitoring

### 1. Política de Alerta: Pub/Sub - Publish requests
- **Nombre:** Pub/Sub - Publish requests
- **Título de la Alerta:** Pub Sub 5 solicitudes falladas en un rango de 5 minutos.
- **Umbral de Fallos:** 5 solicitudes dentro de un periodo de tiempo de 5 minutos.
- **Tipo:** Warning
- **Descripción:**
  - Esta política de alerta monitorea la cantidad de solicitudes de publicación realizadas a un tema específico de Pub/Sub en Google Cloud. Se activará si se detectan 5 o más solicitudes fallidas dentro de un periodo de 5 minutos.

### 2. Política de Alerta: Cloud Run Revision - Request Latency
- **Nombre:** Cloud run revision - Request Latency
- **Título de la Alerta:** Cloud run latencia de 50ms en un periodo de tiempo de 5 minutos.
- **Umbral de Latencia:** 50ms
- **Tipo:** Warning
- **Descripción:**
  - Esta política de alerta monitorea la latencia de las solicitudes que llegan a la revisión de una aplicación en Cloud Run. Se activará si la latencia supera los 50ms durante un periodo de 5 minutos.

### 3. Política de Alerta: Cloud Run Revision - Container CPU Utilization
- **Nombre:** Cloud run revision - Container CPU Utilization
- **Título de la Alerta:** Cloud run utilizacion de CPU sobrepasa el 80% en un periodo de 5 minutos
- **Umbral de uso de CPU:** 80%
- **Tipo:** Warning
- **Descripción:**
  - Esta política de alerta monitorea la utilización de la CPU entre todos los contenedores en ejecución en todas las instancias de contenedor en Cloud Run. Se activará si la utilización de la CPU supera el 80% durante un periodo de 5 minutos.

### 4. Política de Alerta: Cloud Run Revision - Container Memory Utilization
- **Nombre:** Cloud run revision - Container Memory Utilization
- **Título de la Alerta:** Cloud run utilización de la memoria sobrepasa el 80% en un periodo de 5 minutos
- **Umbral de uso de Memoria:** 80%
- **Tipo:** Warning
- **Descripción:**
  - Esta política de alerta monitorea la utilización de la memoria entre todos los contenedores en ejecución en todas las instancias de contenedor en Cloud Run. Se activará si la utilización de la memoria supera el 80% durante un periodo de 5 minutos.

### [Collection Postman](https://github.com/juanca-uniandes/idrl/blob/main/CLOUD%20VIDEOS%20MGMT.postman_collection.json)
  - **Verificar el despliegue:**
  - Todos los endpoints que se detallan a continuación requieren el encabezado `Content-Type: application/json`:

    1. **Registro de usuario:**
      - Realiza una solicitud POST a `http://<IP_PUBLICA_WEB_SERVER>/auth/signup` con un cuerpo que contenga los siguientes campos:
      ```json
      {
          "username": "admin",
          "email": "admin@gmail.com",
          "password": "Admin123",
          "password_2": "Admin123"
      }
      ```

    2. **Obtener token de acceso:**
      - Realiza una solicitud POST a `http://<IP_PUBLICA_LOAD_BALANCING>/auth/login` con un cuerpo que contenga el email y la contraseña del usuario. Ejemplo:
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
      - Realiza una solicitud POST a `http://<IP_PUBLICA_WEB_SERVER>/tasks` con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso anterior. En el cuerpo de la solicitud, proporciona la URL del video que se va a procesar. Por ejemplo:
      ```bash
      curl --location 'http://<IP_PUBLICA_WEB_SERVER>/tasks' \
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
      - Realiza una solicitud GET a http://<IP_PUBLICA_WEB_SERVER>/tasks?max=4&order=1 con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - El parametro "max" indica el numero maximo de registros
      - El parametro "order" especifica el orden en que se muestran los datos, 0 si es ascendete y 1 si es descendente
      - Ejemplo:
    ```
    curl --location 'http://<IP_PUBLICA_WEB_SERVER>/tasks?max=4&order=1' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```
    5. **Consultar estado de una tarea**
      - Realiza una solicitud GET a http://<IP_PUBLICA_WEB_SERVER>/tasks/<ID_TASK> con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - ID-TASK es el codigo de la tarea 
      - Ejemplo:
    ```
    curl --location 'http://<IP_PUBLICA_WEB_SERVER>/tasks/bf5ae39c-751a-439f-9a03-88a19e20c360' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```
  
    6. **Abortar una tarea:**
      - Realiza una solicitud DELETE a http://<IP_PUBLICA_WEB_SERVER>/tasks/<ID_TASK> con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - ID-TASK es el codigo de la tarea, que se puede obtener de la consulta especificada en el paso (4)
      - Ejemplo:
    ```
    curl -X DELETE --location 'http://<IP_PUBLICA_WEB_SERVER>/tasks/bf5ae39c-751a-439f-9a03-88a19e20c360' \
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
      - Realiza una solicitud POST a `http://<IP_PUBLICA_WEB_SERVER>/auth/signup` con un cuerpo que contenga los siguientes campos:
      ```json
      {
          "username": "admin",
          "email": "admin@gmail.com",
          "password": "Admin123",
          "password_2": "Admin123"
      }
      ```

    2. **Obtener token de acceso:**
      - Realiza una solicitud POST a `http://<IP_PUBLICA_WEB_SERVER>/auth/login` con un cuerpo que contenga el email y la contraseña del usuario. Ejemplo:
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
      - Realiza una solicitud POST a `http://<IP_PUBLICA_WEB_SERVER>/tasks` con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso anterior. En el cuerpo de la solicitud, proporciona la URL del video que se va a procesar. Por ejemplo:
      ```bash
      curl --location 'http://<IP_PUBLICA_WEB_SERVER>/tasks' \
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
      - Realiza una solicitud GET a http://<IP_PUBLICA_WEB_SERVER>/tasks?max=4&order=1 con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - El parametro "max" indica el numero maximo de registros
      - El parametro "order" especifica el orden en que se muestran los datos, 0 si es ascendete y 1 si es descendente
      - Ejemplo:
    ```
    curl --location 'http://<IP_PUBLICA_WEB_SERVER>/tasks?max=4&order=1' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```
    5. **Consultar estado de una tarea**
      - Realiza una solicitud GET a http://<IP_PUBLICA_WEB_SERVER>/tasks/<ID_TASK> con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - ID-TASK es el codigo de la tarea 
      - Ejemplo:
    ```
    curl --location 'http://<IP_PUBLICA_WEB_SERVER>/tasks/bf5ae39c-751a-439f-9a03-88a19e20c360' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```
  
    6. **Abortar una tarea:**
      - Realiza una solicitud DELETE a http://<IP_PUBLICA_WEB_SERVER>/tasks/<ID_TASK> con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - ID-TASK es el codigo de la tarea, que se puede obtener de la consulta especificada en el paso (4)
      - Ejemplo:
    ```
    curl -X DELETE --location 'http://<IP_PUBLICA_WEB_SERVER>/tasks//bf5ae39c-751a-439f-9a03-88a19e20c360' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```


