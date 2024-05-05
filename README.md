# Arquitectura
Se ha desplegado en GCP una de base de datos y 3 maquinas virtuales en GCP las cuales se encuentran en el mismo segmento de red. En cada instancia se han desplegado los contenedores previamente desarrollados de modo que funcionen de manera independiente en cada maquina virtual.

![image](https://github.com/juanca-uniandes/idrl/assets/142316997/f26aa9ba-cdd8-4b99-a0ff-8c33e5af70fc)



La distribucion de los componentes se detalla a continuacion:
- **Load Balancing:**
    - Configuracion de distribucion de cargas para los servidores del web-server configurados en el autoscaling.
    - Distribulle 50 solicitudes por instancia.
- **Autoscaling:**
    - Crea multiples instancias del web-server con base en Métricas de ajuste de escala automático: Uso del balanceo de cargas de HTTP: 75%.
    - Crea entre minimo 1 instancia y 3 instancias.
- **Web-Server:**
    - Contenedor Nginx: Configurado como un proxy, para atender las peticiones del usuario,
    - Autorization: Su labor principal es autenticar al usuario con el proposito de proteger a los endpoins que deban estar autorizados.
- **Worker-Server:**
    - Worker: Lleva a cabo la tarea mas "pesada" del sistema, el procesamiento de videos
    - Tasks: Se ocupa de tareas mas livianas, llevadas a cabo de manera sincrona, por ejemplo consultar el estado de una tarea.
    - Redis: Cola de mensajes para llevar a cado las tareas asincronas.
- **Cloud Storage::**
Se encarga de almacenar los videos descargados y procesados
- **Cloud SQL:**
Instancia de base de datos en Postgres
- **Monitoring:**
Atravez de politas monitorea los servicios del autoscaling, grupo de instancias segun varios parametros y de forma grafica.

### Tecnologías asociadas
- Docker
- Flask
- Redis
- Celery
- PostgreSQL
- JMeter



# Pasos para el despliegue del proyecto en Ambiente Cloud GCP
## Preparación del proyecto
-------------------------------------------------------------------------------
### 1. Nuevo proyecto
-------------------------------------------------------------------------------
Antes de comenzar con la configuración, asegúrate de tener un nuevo proyecto creado en Google Cloud Platform (GCP).

1. Accede al menú de "Compute Engine" en GCP.
2. Habilita la API de "Compute Engine".

-------------------------------------------------------------------------------
### 2. VPC network -> Crear una regla de firewall
-------------------------------------------------------------------------------
Para permitir el tráfico entrante a tu instancia, necesitas configurar reglas de firewall.

1. Accede al menú "VPC network" y selecciona "Firewall".
2. Crea una nueva regla de firewall con los siguientes detalles:
   - Nombre: default-allow-http
   - Etiquetas del servidor: http-server
   - Rangos de direcciones IPv4 fuente: 0.0.0.0/0
   - Protocolos y puertos especificados: TCP / todos

-------------------------------------------------------------------------------
### 3. VPC network -> Crear una regla de firewall
-------------------------------------------------------------------------------
Además de la regla anterior, necesitarás otra para permitir el tráfico de comprobación de estado.

1. Accede al menú "VPC network" y selecciona "Firewall".
2. Crea una nueva regla de firewall con los siguientes detalles:
   - Nombre: default-allow-health-check
   - Etiquetas del servidor: http-server
   - Rangos de direcciones IPv4 fuente: 130.21.0.0/22, 35.191.0.0/16
   - Protocolos y puertos especificados: TCP / todos
   - 
## Cloud SQL

      - **Cloud SQL
  - Consideraciones: Si el sistema operativo es Windows, debes reemplazar la línea `CMD ["./wait-for-it.sh", "postgres:5432", "--", "python", "app.py"]` por `CMD ["python", "app.py"]`, y comentar la linea `RUN chmod +x wait-for-it.sh`  en el archivo `postgres-queries/Dockerfile`, adicional tambien debes comentar la linea `command: ["./wait-for-it.sh", "postgres:5432", "--", "python", "app.py"]` en el archivo `docker-compose.yml`. Luego, ejecuta nuevamente el contenedor `postgres-queries` después de que `docker-compose up` haya finalizado todo el despliegue. Esta consideración no es necesaria en sistemas operativos como Ubuntu y macOS.
  - Para que la el web-server y el worker-server enlacen con la base de datos local, se debe entrar a los archivos `.env` ubicados en las carpetas `web-server`,`worker-server`, remplazar el host por `postgres` y el port por `5432`

## Servidor Worker-server

-------------------------------------------------------------------------------
### 1. Computer engine -> Crear una VM
-------------------------------------------------------------------------------
Configura una instancia virtual para alojar tu aplicación.

1. Accede al menú "Compute Engine" y selecciona "VM Instances".
2. Crea una nueva instancia con los siguientes detalles:
   - Nombre: worker-server
   - Región: us-central1
   - Zona: us-central1-a
   - Tipo de máquina: EC - e2-small (2 vCPU, 2 GB de RAM y 20 GB de almacenamiento)
   - Disco de arranque: Imágenes públicas -> Sistema operativo: Ubuntu 20.04 LTS, Seleccionar la regla de conservar el disco de arranque.
   - Configura las reglas de firewall para permitir el tráfico HTTP, HTTPS y comprobaciones de estado del balanceador de carga.
   - Etiqueta de red: http-server
   - Interfaces de red - Dirección IPv4 interna principal - Efimera(Personalizada): 10.128.0.3

-------------------------------------------------------------------------------
### 2. Computer engine -> SSH a la VM worker-server
-------------------------------------------------------------------------------
Accede a la instancia de VM recién creada para instalar Docker y configurar tu aplicación.

1. Accede a la VM utilizando SSH.
2. Ejecuta los siguientes comandos para instalar Docker, clonar tu repositorio y levantar tu aplicación.

```bash
sudo apt-get update -y &&\
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common &&\
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - &&\
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" &&\
sudo apt-get update -y &&\
sudo apt-get install docker-ce docker-ce-cli containerd.io -y &&\
sudo usermod -aG docker $USER &&\
git clone https://github.com/juanca-uniandes/idrl.git &&\
cd idrl/worker-server &&\
```
Por politicas de privacidad y seguridad de github no es posible subir un archivo que se requiere para ingresar al bucket desde el worker-server, por consiguiente de manera manual se debe crear un archivo con nombre “credentials-mgmt.json”, copiar y pegar los datos del json que se encuentran dentro del siguiente pdf y guardar el archivo.

[Documentacion_acceso_Bucked.pdf](https://github.com/juanca-uniandes/idrl/files/15214314/Documentacion_acceso_Bucked.pdf)

Una ves realizado este proceso correctamente se procede a continuar con los pasos. 
```bash
sudo docker compose up -d &&\
sudo docker ps -a  &&\
sudo systemctl enable docker.service &&\
sudo docker update --restart=always worker-server-worker-1 &&\
sudo docker update --restart=always worker-server-redis-1 &&\
sudo docker update --restart=always worker-server-tasks-1 &&\
```
## CLOUD STORAGE - BUCKETS

A continuacion se detallan los pasos necesarios para crear y conectar un bucket de Google Cloud Storage a una instancia de Compute Engine en Google Cloud Platform (GCP).


-------------------------------------------------------------------------------
## 1. Cloud Storage - Create a Bucket
-------------------------------------------------------------------------------

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

-------------------------------------------------------------------------------
## 2. Configurar los Permisos del Bucket
-------------------------------------------------------------------------------

1. Una vez creado el bucket, selecciona el bucket recién creado.
2. Ve a la pestaña "Permisos".
3. Haz clic en el botón "Agregar miembro".
4. Ingresa el nombre de la cuenta de servicio asociada a tu instancia de Compute Engine.
5. Selecciona el rol apropiado para la cuenta de servicio (por ejemplo, "Storage Object Creator" o "Storage Object Admin").
6. Haz clic en el botón "Guardar".

-------------------------------------------------------------------------------
## 3. Crear una Instancia de Compute Engine - Worker-Server
-------------------------------------------------------------------------------

1. En el menú de navegación, selecciona "Compute Engine" > "VM Instances".
2. Haz clic en el botón "Crear instancia".
3. Para la cual vamos a verificar el apartado del Worker-Server.
4. En la sección "Identidad y Acceso a la API", selecciona la cuenta de servicio que tiene permisos sobre el bucket creado anteriormente.
5. Haz clic en el botón "Crear".

-------------------------------------------------------------------------------
## 4. Conectarse a la Instancia por SSH
-------------------------------------------------------------------------------

1. Una vez que la instancia esté creada, haz clic en el botón de SSH para conectarte a la instancia.
2. Se abrirá una ventana de terminal con la conexión SSH a tu instancia.

-------------------------------------------------------------------------------
## 5. Copiar Archivos entre la Instancia y el Bucket
-------------------------------------------------------------------------------

1. Desde la instancia de Compute Engine, utiliza el comando `gsutil` para copiar archivos hacia o desde el bucket de Cloud Storage.
   - Para copiar un archivo desde la instancia a un bucket: `gsutil cp archivo.txt gs://nombre-del-bucket`.
   - Para copiar un archivo desde un bucket a la instancia: `gsutil cp gs://nombre-del-bucket/archivo.txt .` (el punto final indica el directorio actual).

-------------------------------------------------------------------------------
## 6. Verificar la Conexión
-------------------------------------------------------------------------------

1. Copia un archivo desde la instancia de Compute Engine al bucket de Google Cloud Storage utilizando `gsutil`.
2. Verifica que el archivo se haya copiado correctamente accediendo al bucket a través del [Console de Google Cloud Platform](https://console.cloud.google.com/).

## AutoScaling

-------------------------------------------------------------------------------
### 1. Computer engine -> Crear una VM
-------------------------------------------------------------------------------
Configura una instancia virtual para alojar tu aplicación.

1. Accede al menú "Compute Engine" y selecciona "VM Instances".
2. Crea una nueva instancia con los siguientes detalles:
   - Nombre: web-server
   - Región: us-central1
   - Zona: us-central1-a
   - Tipo de máquina: EC - e2-small (2 vCPU, 2 GB de RAM y 20 GB de almacenamiento)
   - Disco de arranque: Imágenes públicas -> Sistema operativo: Ubuntu 20.04 LTS, Seleccionar la regla de conservar el disco de arranque.
   - Configura las reglas de firewall para permitir el tráfico HTTP, HTTPS y comprobaciones de estado del balanceador de carga.
   - Etiqueta de red: http-server

-------------------------------------------------------------------------------
### 2. Computer engine -> SSH a la VM web-server
-------------------------------------------------------------------------------
Accede a la instancia de VM recién creada para instalar Docker y configurar tu aplicación.

1. Accede a la VM utilizando SSH.
2. Ejecuta los siguientes comandos para instalar Docker, clonar tu repositorio y levantar tu aplicación.

```bash
sudo apt-get update -y &&\
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common &&\
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add - &&\
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" &&\
sudo apt-get update -y &&\
sudo apt-get install docker-ce docker-ce-cli containerd.io -y &&\
sudo usermod -aG docker $USER &&\
git clone https://github.com/juanca-uniandes/idrl.git &&\
cd idrl/web-server &&\
sudo docker compose up -d &&\
sudo docker ps -a  &&\
sudo systemctl enable docker.service &&\
sudo docker update --restart=always web-server-app-1 &&\
sudo docker update --restart=always web-server-nginx-1 &&\
```



** Se debe tener encuenta que la IP interna del worker-server sea 10.128.0.3, en caso de no tener esta ip, se deben ejecutar estos comandos después de haber clonado el repositorio.

```bash
cd idrl/web-server/app &&\
nano app.py
```
Una vez abra el app.py se debe modificar esta linea de código con la IP interna perteneciente al worker-server.
```nano de app.py
# URL del servidor que realiza las tareas
TASKS_URL = 'http://IP_WORKER_SERVER:5004/tasks'
```
una ves hecho se guarda el archivo y se deben seguir ejecutando los comandos siguientes a clonar el repositorio.

-------------------------------------------------------------------------------
### 3. Computer engine -> Seleccionar web-server
-------------------------------------------------------------------------------
Después de configurar la VM y tu aplicación, verifica su funcionamiento y realiza las configuraciones adicionales necesarias.

1. Accede a la VM web-server `http://34.122.54.87:5000`. Te dará una respuesta: BASE OK OK OK!
2. Verifica que la aplicación esté funcionando correctamente.
3. Configura las opciones de eliminación de la instancia, como mantener el disco de arranque al eliminar la instancia y elimina la instancia.
4. Verificar que el disco aun exista en la sección "Disk"


-------------------------------------------------------------------------------
### 4. Computer engine -> Seleccionar imágenes
-------------------------------------------------------------------------------
Antes de crear plantillas de instancia, asegúrate de tener una imagen personalizada creada.

1. Accede al menú "Compute Engine" y selecciona "Images".
2. Crea una nueva imagen con el disco de la instancia web-server con la siguiente configuración.

   - name: mywebserver
   - source: disk
   - source disk: web-server

-------------------------------------------------------------------------------
### 5. Computer engine -> Plantillas de instancia
-------------------------------------------------------------------------------
Utiliza plantillas de instancia para simplificar la creación de instancias futuras.

1. Accede al menú "Compute Engine" y selecciona "Instance Templates".
2. Crea una nueva plantilla con los detalles de la imagen personalizada y las reglas de firewall necesarias con la siguiente configuración.
   - name: mywebserver-template
   - machine type: E2-Small
   - boot disk -> change -> custom images -> image: mywebserver
   - Firewall: Allow HTTP Traffic
   - Firewall: Allow HTTPS Traffic
   - Firewall: Allow Load Balancer Health Checks
   - Advanced options -> Networking -> server tags: http-server

-------------------------------------------------------------------------------
### 6. Computer engine -> Grupos de instancias
-------------------------------------------------------------------------------
Crea grupos de instancias para facilitar la gestión y el escalado automático de tus aplicaciones.

1. Accede al menú "Compute Engine" y selecciona "Instance Groups".
2. Crea un nuevo grupo de instancias con la plantilla previamente creada y configura el autoescalado y la auto-curación según sea necesario, con la siguiente configuración.

   - name: us-central1-mig
   - Instance template: mywebserver-template
   - Location: single zone
   - Region: us-central1
   - Zones: us-central1-c
   - Autoscaling: On
   - Minimum number of instance: 1
   - Maximum number of instance: 3
   - Edit-signal->signal type: HTTP Load balancing utilization
   - Edit-signal->target HTTP load balancing utilization: 75
   - Autohealing-> create health check->name: http-health-check
   - Autohealing-> create health check->scope: global
   - Autohealing-> create health check->scope->protocol: TCP
   - Autohealing-> create health check->scope->port: 5000
   - Initial Delay: 60

Create:
   - Autoscaling configuration is not complete: COMFIRM

** Al terminar esto se debe generar una instancia con la imagen templete creada, en la cual puedes validar el estado de la aplicación con la IP externa.

## Load Balancing

-------------------------------------------------------------------------------
### 1. Network services -> Balanceo de carga
-------------------------------------------------------------------------------
Configura un balanceador de carga para distribuir el tráfico entre tus instancias.

1. Accede al menú "Network services" y selecciona "Load Balancing".
2. Crea un nuevo balanceador de carga de aplicación con los detalles adecuados, incluida la configuración del backend y la comprobación de estado, con la siguiente configuración.

   - Application Load Balancer (HTTP/HTTPS)
   - Public facing (external)
   - Best for global workloads
   - Global external Application Load Balancer
   - name: http-lb
   - backend->create backend service->name: http-backend
   - backend->create backend service->backend type: Instance group
   - backend->create backend service->instance group: us-central1-mig
   - backend->create backend service->port numbers: 5000
   - backend->create backend service->balancing mode: rate
   - backend->create backend service->balancing mode->rate: Maximum RPS (50)
   - backend->create backend service->balancing mode->rate: capacidad 80 
   - backend->Health check: http-health-check
   - backend->cloud armor policies:default-security-policy-for-backend-service-http-backend

Create


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
  - **Hostname:** 34.36.153.134
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


