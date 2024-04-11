from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip
import psycopg2

app = Flask(__name__)

UPLOAD_FOLDER = 'videos/uploads'
UPLOAD_FOLDER_TO_PROCESSED_VIDEOS = 'videos/processed'
ALLOWED_EXTENSIONS = {'mp4'}

# Obtener las variables de entorno
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")

# Conexión a la base de datos
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)

# Path to the logo image
LOGO_PATH = 'logo.jpg'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_TO_PROCESSED_VIDEOS'] = UPLOAD_FOLDER_TO_PROCESSED_VIDEOS


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def shorten_video_duration(video_clip, start, end):
    return video_clip.subclip(start, end)


def add_logo_to_video(video_clip):
    logo_clip = ImageClip(LOGO_PATH, duration=1)
    return concatenate_videoclips([logo_clip, video_clip, logo_clip])


def resize_video_to_16_9(video_clip):
    width, _ = video_clip.size
    height = int(width * 9 / 16)
    return video_clip.resize(height=height).crop(x_center=width / 2, y_center=height / 2, width=width, height=height)


def save_processed_video(video_clip, filename):
    processed_filename = filename
    processed_video_path = os.path.join(app.config['UPLOAD_FOLDER_TO_PROCESSED_VIDEOS'], processed_filename)
    video_clip.write_videofile(processed_video_path, codec='libx264', fps=24)
    return processed_video_path

def process_video(file):
    #TODO notificar en base de datos que el video va a ser procesado (JUAN)
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    original_video = VideoFileClip(file_path)
    total_duration = original_video.duration
    start_time = 0

    if total_duration <= 20:
        # Procesar el video completo
        processed_video = shorten_video_duration(original_video, 0, total_duration)
        processed_video = add_logo_to_video(processed_video)
        processed_video = resize_video_to_16_9(processed_video)
        # TODO notificar en base de datos que el video fue procesado completamente (JUAN)
        save_processed_video(processed_video, filename)
    else:
        # Procesar por partes
        for i in range(0, int(total_duration), 20):
            processed_clip = shorten_video_duration(original_video, start_time, start_time + 20)
            processed_clip = add_logo_to_video(processed_clip)
            processed_clip = resize_video_to_16_9(processed_clip)

            # Generate filename with start time
            clip_filename = os.path.splitext(filename)[0] + f'_part_{start_time}.mp4'

            # TODO notificar en base de datos que el video fue procesado completamente (JUAN)
            save_processed_video(processed_clip, clip_filename)

            # Increment start_time
            start_time += 20

    return True

# def executeQuery(query, params):
#     cursor = conn.cursor()
#     cursor.execute(query, params)
#     conn.commit()
#     cursor.close()
#     return "Query executed successfully"


#TODO eliminar estas funciones de prueba cuando el contendor load y files
# esten terminados(JUAN)
############## INICIO Solo para pruebas NO PRESTAR ATENCION A ESTO
@app.route('/upload-form', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            process_video(file)
            return render_template('success.html')
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
############## FIN Solo para pruebas NO PRESTAR ATENCION A ESTO

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
