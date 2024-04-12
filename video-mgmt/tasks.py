# tasks.py
from celery import Celery
import time
import psycopg2
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip


broker_url = 'redis://redis:6379/0'
app = Celery('tasks', backend='rpc://', broker=broker_url)

# Obtener las variables de entorno
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = 5432

UPLOAD_FOLDER = 'videos/uploads'
UPLOAD_FOLDER_TO_PROCESSED_VIDEOS = 'videos/processed'
ALLOWED_EXTENSIONS = {'mp4'}
LOGO_PATH = 'logo.jpg'

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
    processed_video_path = os.path.join(UPLOAD_FOLDER_TO_PROCESSED_VIDEOS, processed_filename)
    video_clip.write_videofile(processed_video_path, codec='libx264', fps=24)
    return processed_video_path


def process_video(file):
    #TODO notificar en base de datos que el video va a ser procesado (JUAN)
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
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

def insert_video(task_id, url):
    # Conexión a la base de datos 'idrl_db'
    db_params = {
        'dbname': "idrl_db",
        'user': "idrl_user",
        'password': "idrl_2024",
        'host': "postgres"
    }

    # Create a cursor object
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    # Insert a record into the videos table
    insert_query = """
        INSERT INTO videos (video_name, path, user_id, duration, loaded_at, processed_at, url, task_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    video_name = "example_video.mp4"
    path = "/path/to/video/example_video.mp4"
    user_id = 1  # Assuming user_id is 1
    duration = 3600  # Duration in seconds
    loaded_at = datetime.now()
    processed_at = None  # Assuming the video is not processed yet
    url = url
    task_id = task_id

    cur.execute(insert_query, (video_name, path, user_id, duration, loaded_at, processed_at, url, task_id))

    conn.commit()

    cur.close()
    conn.close()

def insert_split_video(order_video):
    # Conexión a la base de datos 'idrl_db'
    db_params = {
        'dbname': "idrl_db",
        'user': "idrl_user",
        'password': "idrl_2024",
        'host': "postgres"
    }

    # Create a cursor object
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    # Insert a record into the videos table
    insert_query = """
        INSERT INTO split_videos (id_video, split_path, _order)
        VALUES (%s, %s, %s)
    """   

    #Modificar el id del video, considerar id de la tarea creada
    id_video = 1  # Assuming the video_id is 1
    split_path = "/path/to/video/example_video.mp4"
    order = order_video

    # Execute the insert query
    cur.execute(insert_query, (id_video, split_path, order))

    # Commit the transaction
    conn.commit()

    # Close cursor and connection
    cur.close()
    conn.close()


@app.task(bind=True)
def process_video(self, url):
    task_id = self.request.id
    insert_video(task_id, url)
    for i in range(1, 6):
        insert_split_video(i)
        time.sleep(20)
        self.update_state(state='PROGRESS', meta={'progress': i*20})
    #Actualizar estado de la tarea
    return {'status': 'completado!', 'result': 100}