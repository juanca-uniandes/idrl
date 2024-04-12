from flask import Flask, request, jsonify
from functools import wraps
import jwt
import datetime
import requests
from tasks import app as celery_app, process_video

app = Flask(__name__)

# URL del servidor que proporciona el token después del inicio de sesión
LOGIN_URL = 'http://autenticador:5002/login'


# Función de decorador para validar el token JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

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
        return f(*args, **kwargs)

    return decorated

#### Pruebas nginx y JWT ####
@app.route('/task')
def task():
    return 'OK'


@app.route('/task/ok')
@token_required
def index():
    return 'OK OK OK!'
#### ELIMINAR DESPUES DE VALIDADO ####

# Rutas protegidas que requieren un token válido
@app.route('/task/start', methods=['POST'])
@token_required
def start():
    url = request.json['url']    
    task = process_video.delay(url)
    return jsonify({'task_id': str(task.id)}), 202


@app.route('/task/status/<task_id>', methods=['GET'])
@token_required
def status(task_id):
    task = celery_app.AsyncResult(task_id)
    return jsonify({'state': str(task.state), 'info': task.info}), 200


@app.route('/task/abort/<task_id>', methods=['DELETE'])
@token_required
def abort(task_id):
    task = celery_app.AsyncResult(task_id)
    task.revoke(terminate=True)
    return jsonify({'status': 'Task aborted!'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)