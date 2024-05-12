from flask import Flask, request, jsonify
from functools import wraps
import jwt
import datetime
import requests
import base64
import json
import os
from flask import request
from tasks import app as celery_app, process_video
from util import fn_info_tasks, fn_info_task, delete_task

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'mp4'}
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "credentials-cuenta-storage.json"

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

    
#### Pruebas nginx y JWT ####
@app.route('/')
def OK():
    return 'BASE OK OK OK!'

@app.route('/tasks/ok')
def index():
    return 'TASKS OK OK OK!'
#### ELIMINAR DESPUES DE VALIDADO ####


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_token_from_body(token):
    try:
        if not token:
            raise ValueError('Token is missing!')

        # Decodificar el token y extraer la información del usuario
        data = jwt.decode(token, 'videos-mgmt', algorithms=['HS256'])
        current_user = data['user_id']
        
        # Agregar la información del usuario a la solicitud
        request.current_user = current_user
        # Pasar la información del usuario a la función decorada (opcional)
        return current_user
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired!')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token!')

# Rutas protegidas que requieren un token válido
@app.route('/tasks', methods=['POST'])
def start():
    try:
        # Decodificar el cuerpo del mensaje recibido de Pub/Sub
        pubsub_message = json.loads(request.data.decode('utf-8'))

        # Parsear el mensaje JSON
        actual_data = json.loads(pubsub_message['data'])

        token = actual_data.get('Authorization')

        # Obtener el usuario actual a partir del token
        current_user = get_token_from_body(token)

        # Extraer la URL del mensaje
        url = actual_data.get('url')

        if not url:
            return jsonify({'error': 'La URL no puede estar vacía'}), 404
        
        if not allowed_file(url):
            return jsonify({'error': f"El formato del archivo en la URL no está permitido. Se esperaba una extensión de archivo {ALLOWED_EXTENSIONS}"}), 404

        # Si todo está bien, procesar el video
        task = process_video.delay(url, current_user)
        return jsonify({'task_id': str(task.id), 'user': current_user}), 202
    
    except KeyError:
        return jsonify({'error': 'Proporcione una URL'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 401


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
    task = celery_app.AsyncResult(task_id)
    task.revoke(terminate=True)
    result = delete_task(task_id)
    return jsonify({'result': 'Tarea cancelada correctamente'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
