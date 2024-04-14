from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import psycopg2
import os
import re

app = Flask(__name__)

# Obtener las variables de entorno para la conexión a la base de datos
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = 5432

# Función para conectar a la base de datos PostgreSQL
def connect_db():
    return psycopg2.connect(
        dbname="idrl_db",
        user="idrl_user",
        password="idrl_2024",
        host="postgres"
    )

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
