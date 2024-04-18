import os
import jwt
from functools import wraps  # Importa wraps desde functools
from flask import Flask, request, jsonify
import base64

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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
@app.route('/upload')
def task():
    return 'OK'


@app.route('/upload/ok')
@token_required
def index():
    return 'OK OK OK!'
#### ELIMINAR DESPUES DE VALIDADO ####

def save_video(file, folder=None):
    if not folder:
        folder = UPLOAD_FOLDER
    if not os.path.exists(folder):
        os.makedirs(folder)
    file_path = os.path.join(folder, file.filename)
    file.save(file_path)
    return file_path


def clean_filename(filename):
    # Elimina el número y el guion bajo al final del nombre del archivo
    parts = filename.rsplit('_', 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0]
    return filename


@app.route('/upload', methods=['POST'])
def upload_full_video():
    # Obtener el JSON de la solicitud
    json_data = request.json

    # Verificar si el JSON contiene los campos necesarios
    if 'file' not in json_data or 'path_file' not in json_data:
        return jsonify({'message': 'Invalid JSON format', 'status': 400}), 400

    # Obtener el contenido del archivo codificado en base64 y la ruta del archivo del JSON
    file_content_base64 = json_data['file']
    path_file = json_data['path_file']

    # Verificar si se ha proporcionado un archivo
    if not file_content_base64:
        return jsonify({'message': 'No file content provided', 'status': 400}), 400

    # Decodificar el contenido del archivo desde base64
    file_content = base64.b64decode(file_content_base64)

    # Guardar el archivo en la ruta especificada
    with open(path_file, 'wb') as file:
        file.write(file_content)

    # Retornar una respuesta JSON indicando que el video se ha subido exitosamente
    return jsonify({'message': 'Full video uploaded successfully', 'status': 200}), 200

@app.route('/delete', methods=['DELETE'])
def delete_video():
    video_path = request.args.get('video_path', default=None, type=str)
    try:
        if os.path.exists(video_path):
            os.remove(video_path)
            return jsonify({'message': 'video deleted successfully', 'status': 200}), 200
        else:
            return jsonify({'message': f'video not exists: {video_path} ', 'status': 500}), 500
    except Exception as e:
        return jsonify({'message': str(e), 'status': 500}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)