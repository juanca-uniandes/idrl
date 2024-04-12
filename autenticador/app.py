from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import psycopg2
import os

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
@app.route('/register', methods=['POST'])
def register():
    # Obtener datos del cuerpo de la solicitud
    data = request.get_json()
    username = data['username']
    email = data['email']
    password = generate_password_hash(data['password'])

    # Conectar a la base de datos
    connection = connect_db()
    cursor = connection.cursor()

    # Insertar usuario en la base de datos
    cursor.execute("INSERT INTO usuarios (username, email, pass) VALUES (%s, %s, %s)", (username, email, password))
    connection.commit()

    # Cerrar la conexión y el cursor
    cursor.close()
    connection.close()

    return jsonify({'message': 'User registered successfully'})

# Ruta para el inicio de sesión de usuarios
@app.route('/login', methods=['POST'])
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
        return jsonify({'user': {'id': user[0], 'username': user[1], 'email': user[2]}, 'token': token})
    else:
        cursor.close()
        connection.close()
        return jsonify({'message': 'Invalid email or password'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)