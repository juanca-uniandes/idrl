from flask import Flask, request, jsonify
from functools import wraps
import jwt
import datetime
import requests
from tasks import app as celery_app, process_video
from util import fn_info_tasks, fn_info_task, delete_task

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'mp4'}

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
@app.route('/tasks/ok')
@token_required
def index(current_user):
    return 'OK OK OK!'
#### ELIMINAR DESPUES DE VALIDADO ####


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

    task = process_video.delay(url, current_user)
    return jsonify({'task_id': str(task.id), 'user': current_user}), 202


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
    app.run(host='0.0.0.0', port=5004)
