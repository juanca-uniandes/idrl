# tasks.py
from celery import Celery
import time
import psycopg2
from datetime import datetime
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip
import requests


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


def process_saved_video(file_path):
    #TODO notificar en base de datos que el video va a ser procesado (JUAN)
    original_video = VideoFileClip(UPLOAD_FOLDER + '/' + file_path)
    filename = original_video.filename.replace('videos/uploads/', '')
    selectQuery = """
        SELECT * FROM videos WHERE video_name = ?
    """
    result = runQuery(selectQuery, (filename,))
    video_info = result[0]
    print(video_info)

    insertQuery = """
        INSERT INTO processing_videos(id_video, status, created_at, updated_at) VALUES (?, ?, ?, ?)
    """
    runQuery(insertQuery, (video_info['id'], 'Procesando', datetime.now(), datetime.now()))

    total_duration = original_video.duration
    start_time = 0
    split_counter = 0

    if total_duration <= 20:
        # Procesar el video completo
        processed_video = shorten_video_duration(original_video, 0, total_duration)
        processed_video = add_logo_to_video(processed_video)
        processed_video = resize_video_to_16_9(processed_video)
        save_processed_video(processed_video, filename)
        insertQuery = """
            INSERT INTO split_videos(id_video, split_path, _order, created_at, updated_at) VALUES (?, ?, ?, ?, ?)
        """
        runQuery(insertQuery, (video_info['id'], UPLOAD_FOLDER_TO_PROCESSED_VIDEOS + '/' + filename, 1, datetime.now(), datetime.now()))
    else:
        # Procesar por partes
        for i in range(0, int(total_duration), 20):
            processed_clip = shorten_video_duration(original_video, start_time, start_time + 20)
            processed_clip = add_logo_to_video(processed_clip)
            processed_clip = resize_video_to_16_9(processed_clip)

            # Generate filename with start time
            clip_filename = os.path.splitext(filename)[0] + f'_part_{split_counter}.mp4'

            # TODO notificar en base de datos que el video fue procesado completamente (JUAN)
            save_processed_video(processed_clip, clip_filename)

            # Increment start_time
            start_time += 20
            insertQuery = """
                INSERT INTO split_videos(id_video, split_path, _order, created_at, updated_at) VALUES (?, ?, ?, ?, ?)
            """
            runQuery(insertQuery, (
            video_info['id'], UPLOAD_FOLDER_TO_PROCESSED_VIDEOS + '/' + filename, split_counter, datetime.now(), datetime.now()))
            split_counter += 1

    insertQuery = """
        INSERT INTO processing_videos(id_video, status, created_at, updated_at) VALUES (?, ?, ?, ?)
    """
    runQuery(insertQuery, (video_info['id'], 'Procesado', datetime.now(), datetime.now()))
    return True


def insert_video(task_id, url):

    # Insert a record into the videos table
    insert_query = """
        INSERT INTO videos (video_name, path, user_id, duration, loaded_at, processed_at, url, task_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    file_path = download_video_from_url(url, UPLOAD_FOLDER)
    if file_path:
        file = VideoFileClip(file_path)
        video_name = file.filename.replace('videos/uploads/', '')
        duration = file.duration
        path = UPLOAD_FOLDER + "/" + video_name
        user_id = 1
        loaded_at = datetime.now()
        processed_at = None
        video_url = url
        task_id = task_id

        runQuery(insert_query,(video_name, path, user_id, duration, loaded_at, processed_at, video_url, task_id))

        return video_name
    return None


def runQuery(query, params):

    db_params = {
        'dbname': "idrl_db",
        'user': "idrl_user",
        'password': "idrl_2024",
        'host': "postgres"
    }

    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    cur.execute(query, params)

    conn.commit()

    cur.close()
    conn.close()


def download_video_from_url(url, destination_path):
    try:
        file_name = url.split('/')[-1]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_name_with_timestamp = f"{timestamp}_{file_name}"
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
        file_path = os.path.join(destination_path, file_name_with_timestamp)
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"Video downloaded successfully as '{file_name_with_timestamp}' in '{destination_path}'!")
            return file_path
        else:
            print(f"Error downloading the video. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while downloading the video: {str(e)}")
        return None

@app.task(bind=True)
def process_video(self, url):
    task_id = self.request.id
    file_path = insert_video(task_id, url)
    process_saved_video(file_path)
    return {'status': 'completado!', 'result': 100}