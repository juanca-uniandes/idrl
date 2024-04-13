import os
import jwt
from functools import wraps  # Importa wraps desde functools
from flask import Flask, request, jsonify

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
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    json_data = request.json
    if file.filename == '':
        return 'No selected file'
    if file:
        save_video(file, json_data['path_file'])
        return 'Full video uploaded successfully'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)