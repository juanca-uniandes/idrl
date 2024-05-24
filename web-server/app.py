from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import json
import datetime
import random
import psycopg2
import requests
from google.cloud import pubsub_v1, logging
import time
import os
import re
from util import fn_info_tasks, fn_info_task, delete_task

app = Flask(__name__)

project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
topic_id = os.getenv('PUBSUB_TOPIC')
tasks_url = os.getenv('TASKS_URL')

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials-cuenta-storage.json"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

# Configuración de Google Cloud Logging
logging_client = logging.Client()
logger = logging_client.logger("pubsub_logger")

# Función para conectar a la base de datos PostgreSQL
def connect_db():
    return psycopg2.connect(
        dbname="idrl_db",
        user="idrl_user",
        password="idrl_2024",
        host="161.132.40.204",
        port="5433"
    )

# URL del servidor que realiza las tareas

#EXTENCION de los videos
ALLOWED_EXTENSIONS = {'mp4'}

@app.route('/')
def index():
    random_value = random.uniform(0, 0.5)
    time.sleep(random_value)
    return 'BASE OK OK OK!'
#### Pruebas nginx y JWT ####

@app.route('/tasks/ok')
def indextasks():
    random_value = random.uniform(0, 0.5)
    time.sleep(random_value)
    return 'TASKS OK OK OK!'
#### ELIMINAR DESPUES DE VALIDADO ####

# Función de decorador para validar el token JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        current_user = None

        # Verificar si el token está presente en el encabezado Authorization
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Decodificar el token y extraer la información del usuario
            data = jwt.decode(token, 'videos-mgmt', algorithms=['HS256'])
            current_user = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

        # Agregar la información del usuario a la solicitud
        request.current_user = current_user

        # Pasar la información del usuario a la función decorada (opcional)
        return f(current_user, *args, **kwargs)

    return decorated



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Ruta para el registro de usuarios
@app.route('/auth/signup', methods=['POST'])
def signup():
    # Obtener datos del cuerpo de la solicitud
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    password_2 = data.get('password_2')

    # Verificar si todos los campos están presentes en la solicitud
    if not (username and email and password and password_2):
        return jsonify({'message': 'Todos los campos son obligatorios'}), 400

    # Verificar si la contraseña coincide con la confirmación de la contraseña
    if password != password_2:
        return jsonify({'message': 'Las contraseñas no coinciden'}), 400

    # Verificar si la contraseña cumple con los lineamientos mínimos de seguridad
    if len(password) < 8:
        return jsonify({'message': 'El usuario no pudo ser creado la contraseña debe tener al menos 8 caracteres'}), 400
    if not re.search(r'[A-Z]', password):
        return jsonify({'message': 'El usuario no pudo ser creado la contraseña debe contener al menos una letra mayúscula'}), 400
    if not re.search(r'[a-z]', password):
        return jsonify({'message': 'El usuario no pudo ser creado la contraseña debe contener al menos una letra minúscula'}), 400
    if not re.search(r'[0-9]', password):
        return jsonify({'message': 'El usuario no pudo ser creado la contraseña debe contener al menos un dígito'}), 400

    # Conectar a la base de datos y verificar si el nombre de usuario y el correo electrónico ya existen
    connection = connect_db()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
    if cursor.fetchone():
        cursor.close()
        connection.close()
        return jsonify({'message': 'El usuario no pudo ser creado el nombre de usuario ya existe'}), 400

    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        connection.close()
        return jsonify({'message': 'El usuario no pudo ser creado el Email ya existe'}), 400

    # Insertar usuario en la base de datos
    hashed_password = generate_password_hash(password)
    cursor.execute("INSERT INTO usuarios (username, email, pass) VALUES (%s, %s, %s)", (username, email, hashed_password))
    connection.commit()

    # Cerrar la conexión y el cursor
    cursor.close()
    connection.close()

    return jsonify({'message': 'Usuario registrado exitosamente'}), 201

# Ruta para el inicio de sesión de usuarios
@app.route('/auth/login', methods=['POST'])
def login():
    # Obtener datos del cuerpo de la solicitud
    data = request.get_json()
    email = data['email']
    password = data['password']

    # Conectar a la base de datos
    connection = connect_db()
    cursor = connection.cursor()

    # Buscar usuario en la base de datos por correo electrónico
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()

    # Verificar si el usuario existe y si la contraseña es correcta
    if user and check_password_hash(user[3], password):
        # Generar token JWT
        token = jwt.encode({'user_id': user[0], 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, 'videos-mgmt')
        cursor.close()
        connection.close()
        # Devolver el token y la información del usuario como parte de la respuesta
        # return jsonify({'user': {'id': user[0], 'username': user[1], 'email': user[2]}, 'token': token})
        return jsonify({'token': token})
    else:
        cursor.close()
        connection.close()
        return jsonify({'message': 'Correo electrónico o contraseña no válidos'}), 401

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Rutas protegidas que requieren un token válido
@app.route('/tasks', methods=['POST'])
@token_required
def publish_message(current_user):
    try:
        # Obtener el cuerpo de la solicitud JSON
        data = request.get_json()
        if not data or 'url' not in data:
            logger.log_text('Bad Request: no URL provided', severity="ERROR")
            return jsonify({'error': 'Bad Request: no URL provided'}), 400

        # Obtener la URL del cuerpo de la solicitud
        url = data['url'] 

        if not url:
            return jsonify({'error': 'La URL no puede estar vacía'}), 404
        
        if not allowed_file(url):
            return jsonify({'error': f"El formato del archivo en la URL no está permitido. Se esperaba una extensión de archivo {ALLOWED_EXTENSIONS}"}), 404

        # Crear el objeto JSON a enviar con la URL cargada
        message_obj = {'url': url}

        # Convertir el objeto JSON a string
        message_str = json.dumps(message_obj)
        
        # Log el mensaje antes de publicarlo
        logger.log_text(f"Publishing message: {message_str}")
        # Convertir el objeto JSON a una cadena de bytes
        message_bytes = message_str.encode('utf-8')

        # Publicar el mensaje en Pub/Sub
        future = publisher.publish(topic_path, message_bytes)
        future.result()

        return jsonify({'message': 'URL published successfully'}), 200
    except Exception as e:
        # Log la excepción en caso de error
        logger.log_text(f"Error publishing URL: {str(e)}", severity="ERROR")
        return jsonify({'error': str(e)}), 500

@app.route('/tasks', methods=['GET'])
@token_required
def status_all(current_user):
    max = request.args.get('max', default=None, type=int)
    order = request.args.get('order', default=None, type=int)    
    results = fn_info_tasks(max, order)
    if results:
        data = [{'task_id': row[0], 'status': row[1]} for row in results]
        return jsonify(data)        
    else:
        return jsonify({'error': 'Error al ejecutar el procedimiento almacenado'}), 500

@app.route('/tasks/<task_id>', methods=['GET'])
@token_required
def status_id(current_user, task_id):    
    results = fn_info_task(task_id)
    if results:
        data = [{'task_id': row[0], 'status': row[1], 'url': row[2]} for row in results]
        return jsonify(data)
    else:
        return jsonify({'error': 'Error al ejecutar el procedimiento almacenado'}), 500

@app.route('/tasks/<task_id>', methods=['DELETE'])
@token_required
def abort(current_user, task_id):
    try:
        # Verificar si la tarea existe antes de intentar eliminarla
        existing_task = fn_info_task(task_id)
        if not existing_task:
            return jsonify({'error': 'La tarea especificada no existe'}), 404

        # Realizar la solicitud DELETE al servidor de tareas
        response = requests.delete(tasks_url + '/tasks/' + task_id)

        # Manejar la respuesta de la solicitud DELETE
        if response.status_code == 200:
            # Si la solicitud DELETE se completó correctamente, eliminar la tarea de la base de datos
            result = delete_task(task_id)
            if result:
                return jsonify({'message': 'Tarea cancelada correctamente'}), 200
            else:
                return jsonify({'error': 'Error al eliminar la tarea de la base de datos'}), 500
        else:
            # Si la solicitud DELETE falló, devolver un mensaje de error adecuado
            return jsonify({'error': f'Error al cancelar la tarea: {response.text}'}), response.status_code
    except Exception as e:
        # Manejar cualquier excepción inesperada y devolver un mensaje de error
        return jsonify({'error': f'Error al cancelar la tarea: {str(e)}'}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
