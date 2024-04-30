from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import datetime
import random
import psycopg2
import requests
import time
import os
import re

app = Flask(__name__)

# Obtener las variables de entorno para la conexión a la base de datos
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = 5433

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
TASKS_URL = 'http://10.128.0.3:5004/tasks'

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
def start(current_user):
    try:
        url = request.json['url']
        if not url:
            return jsonify({'error': 'La URL no puede estar vacía'}), 404
    except KeyError:
        return jsonify({'error': 'Proporcione una URL'}), 404
    if not allowed_file(url):
        return jsonify({'error': f"El formato del archivo en la URL no está permitido. Se esperaba una extensión de archivo {ALLOWED_EXTENSIONS}"}), 404
    
    response = requests.post(TASKS_URL, json={'url': url}, headers=request.headers)
    if response.status_code != 202:
        return jsonify({'error': 'Error al iniciar la tarea'}), 500

    # Tarea iniciada correctamente
    return jsonify({'task_id': 'Tarea iniciada correctamente'}), 202


@app.route('/tasks', methods=['GET'])
@token_required
def status_all(current_user):
    max = request.args.get('max', default=None, type=int)
    order = request.args.get('order', default=None, type=int)
    
    response = requests.get(TASKS_URL, headers=request.headers) 
    if response.status_code != 200:
        return jsonify({'error': 'Error al obtener la tarea'}), 500
    return jsonify(response.json())   

@app.route('/tasks/<task_id>', methods=['GET'])
@token_required
def status_id(current_user, task_id): 
    response = requests.get(TASKS_URL+'/'+task_id, headers=request.headers)
    if response.status_code != 200:
        return jsonify({'error': 'Error al obtener la tarea'}), 500
    
    return jsonify(response.json()), 200

    # Devolver la tarea obtenida correctamente


@app.route('/tasks/<task_id>', methods=['DELETE'])
@token_required
def abort(current_user, task_id):
    response = requests.delete(TASKS_URL+'/'+task_id, headers=request.headers)
    if response.status_code != 200:
        return jsonify({'error': 'Error al cancelar la tarea'}), 500
    return jsonify({'result': 'Tarea cancelada correctamente'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)