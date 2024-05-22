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

1. Habilita la API de "Compute Engine".
2. Habilitar el API de "Cloud Run".
3. Habilitar el API de "Pub Sub".
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
#### a. Crear en Cloud Run, un servicio para el web server
1. Modificar el codigo previo ubicado en la carpeta "web-server"
2. Crear el servicio ubicandose en la carpeta correspondiente y ejecutando el siguiente comando:

#### b. Crear en Cloud Run, un servicio para el worker
1. Modificar el codigo previo ubicado en la carpeta "worker-server"
2. Crear el servicio ubicandose en la carpeta correspondiente y ejecutando el siguiente comando:


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
4. Ingresa el nombre de la cuenta de servicio asociada a tu instancia de Compute Engine.
5. Selecciona el rol apropiado para la cuenta de servicio (por ejemplo, "Storage Object Creator" o "Storage Object Admin").
6. Haz clic en el botón "Guardar".

-------------------------------------------------------------------------------
### 7. Pub Sub - Topic, Subscription
-------------------------------------------------------------------------------
Crear el "topic" y "subscription" de acuerdo a las siguientes características:

- Delivery type de tipo "Push"
- El endpoint asociado al punto anterior debe ser la URL del balanceador de carga del worker server
- Esta url debe soportar obligatoriamente el protocolo https

## Proceso de eliminación.

Para evitar gastos inecesarios se pueden eliminar las instancias de la siguiente manera.

-------------------------------------------------------------------------------
### 1. Eliminar -> Para evitar consumo innecesario
-------------------------------------------------------------------------------
Cuando hayas terminado de probar y usar tus recursos, asegúrate de eliminarlos para evitar cargos innecesarios en tu cuenta de GCP.

1. Elimina el balanceador de carga, los grupos de instancias y las instancias virtuales.
   - Network services -> Load Balancing -> http-load -> delete
   - Network services -> Load Balancing -> http-load -> delete ->http-backend
   - cloud armor policies -> default-security-policy-for-backend-service-http-backend -> delete
   - Computer engine -> Instance groups -> us-central1-mig -> delete
   - Computer engine -> Instance VM  -> us-central1-mig-*  -> delete


** Para reinstalar debes volver a realizar el punto 6 del autoscaling y el punto 1 de load balancing. 


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
![image](https://github.com/juanca-uniandes/idrl/assets/142238841/1f3f1fc6-0b30-42d9-8d83-5688ff7ea354)


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

# Monitoreo a través de gráficos

- Gráfico de Capacidad de servicio
- Gráfico de Utilización actual del Autoscaler
- Gráfico de Tamaño del grupo de instancias
  ![image](https://github.com/juanca-uniandes/idrl/assets/142238841/92a74e11-9762-4217-b6bb-b3f1b8b0ca74)

# Monitoreo a través de Verificaciones de tiempo de actividad

- **Verificación de la salud de los servidores en el balanceador de carga en la nube**
  - **Protocolo:** HTTP
  - **Tipo de recurso:** URL
  - **Hostname:** 34.49.16.68 y 34.49.16.68
  - **Frecuencia de la verificación:** 1 minuto
  - **Tiempo de espera de respuesta:** 10 segundos
  - **Registrar fallos de verificación:** Verdadero
  - **Código de respuesta HTTP aceptable:** 2XX
- **Conclusión:** La implementación de una alerta de verificación de latencia con la configuración detallada proporciona un monitoreo casi en tiempo real de la disponibilidad de los servidores. Esto permite una detección temprana de problemas, una respuesta oportuna y, en última instancia, mejora la confiabilidad del sistema al garantizar que los servidores respondan correctamente.

    

### [Collection Postman](https://github.com/juanca-uniandes/idrl/blob/main/CLOUD%20VIDEOS%20MGMT.postman_collection.json)
  - **Verificar el despliegue:**
  - Todos los endpoints que se detallan a continuación requieren el encabezado `Content-Type: application/json`:

    1. **Registro de usuario:**
      - Realiza una solicitud POST a `http://<IP_PUBLICA_LOAD_BALANCING>/auth/signup` con un cuerpo que contenga los siguientes campos:
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
      - Realiza una solicitud POST a `http://<IP_PUBLICA_LOAD_BALANCING>/tasks` con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso anterior. En el cuerpo de la solicitud, proporciona la URL del video que se va a procesar. Por ejemplo:
      ```bash
      curl --location 'http://<IP_PUBLICA_LOAD_BALANCING>/tasks' \
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
      - Realiza una solicitud GET a http://<IP_PUBLICA_LOAD_BALANCING>/tasks?max=4&order=1 con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - El parametro "max" indica el numero maximo de registros
      - El parametro "order" especifica el orden en que se muestran los datos, 0 si es ascendete y 1 si es descendente
      - Ejemplo:
    ```
    curl --location 'http://<IP_PUBLICA_LOAD_BALANCING>/tasks?max=4&order=1' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```
    5. **Consultar estado de una tarea**
      - Realiza una solicitud GET a http://<IP_PUBLICA_LOAD_BALANCING>/tasks/<ID_TASK> con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - ID-TASK es el codigo de la tarea 
      - Ejemplo:
    ```
    curl --location 'http://<IP_PUBLICA_LOAD_BALANCING>/tasks/bf5ae39c-751a-439f-9a03-88a19e20c360' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```
  
    6. **Abortar una tarea:**
      - Realiza una solicitud DELETE a http://<IP_PUBLICA_LOAD_BALANCING>/tasks/<ID_TASK> con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - ID-TASK es el codigo de la tarea, que se puede obtener de la consulta especificada en el paso (4)
      - Ejemplo:
    ```
    curl -X DELETE --location 'http://<IP_PUBLICA_LOAD_BALANCING>/tasks//bf5ae39c-751a-439f-9a03-88a19e20c360' \
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
      - Realiza una solicitud POST a `http://<IP_PUBLICA_LOAD_BALANCING>/auth/signup` con un cuerpo que contenga los siguientes campos:
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
      - Realiza una solicitud POST a `http://<IP_PUBLICA_LOAD_BALANCING>/tasks` con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso anterior. En el cuerpo de la solicitud, proporciona la URL del video que se va a procesar. Por ejemplo:
      ```bash
      curl --location 'http://<IP_PUBLICA_LOAD_BALANCING>/tasks' \
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
      - Realiza una solicitud GET a http://<IP_PUBLICA_LOAD_BALANCING>/tasks?max=4&order=1 con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - El parametro "max" indica el numero maximo de registros
      - El parametro "order" especifica el orden en que se muestran los datos, 0 si es ascendete y 1 si es descendente
      - Ejemplo:
    ```
    curl --location 'http://<IP_PUBLICA_LOAD_BALANCING>/tasks?max=4&order=1' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```
    5. **Consultar estado de una tarea**
      - Realiza una solicitud GET a http://<IP_PUBLICA_LOAD_BALANCING>/tasks/<ID_TASK> con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - ID-TASK es el codigo de la tarea 
      - Ejemplo:
    ```
    curl --location 'http://<IP_PUBLICA_LOAD_BALANCING>/tasks/bf5ae39c-751a-439f-9a03-88a19e20c360' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```
  
    6. **Abortar una tarea:**
      - Realiza una solicitud DELETE a http://<IP_PUBLICA_LOAD_BALANCING>/tasks/<ID_TASK> con autorización de tipo Bearer, utilizando el token de acceso obtenido en el paso de autenticacion.
      - ID-TASK es el codigo de la tarea, que se puede obtener de la consulta especificada en el paso (4)
      - Ejemplo:
    ```
    curl -X DELETE --location 'http://<IP_PUBLICA_LOAD_BALANCING>/tasks//bf5ae39c-751a-439f-9a03-88a19e20c360' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MTMwMjYzMDV9.Q2W2gXVHS0LcjlATjLg_Aj2VTffZTo-xfRn_op2HKUw'
    ```


