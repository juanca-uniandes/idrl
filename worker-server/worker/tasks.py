# tasks.py
from celery import Celery
import time
import psycopg2
from datetime import datetime
import os
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip
import requests
import base64
from flask import Flask, request, jsonify
from util import upload_to_gcs, delete_from_gcs

broker_url = 'redis://redis:6379/0'
app = Celery('tasks', backend='rpc://', broker=broker_url)

# Obtener las variables de entorno
DB_NAME = "idrl_db"
DB_USER = "idrl_user"
DB_PASSWORD = "idrl_2024"
DB_HOST = "161.132.40.204"
DB_PORT = 5433

UPLOAD_FOLDER = 'videos/uploads'
UPLOAD_FOLDER_TO_PROCESSED_VIDEOS = 'videos/processed'
ALLOWED_EXTENSIONS = {'mp4'}
LOGO_PATH = 'logo.png'


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


def process_saved_video(task_id, file_path):
    original_video = VideoFileClip(UPLOAD_FOLDER + '/' + file_path)
    filename = original_video.filename.replace('videos/uploads/', '')
    selectQuery = """
        SELECT * FROM videos WHERE video_name = %s
    """
    result = runQuery(selectQuery, (filename,))
    video_info = result[0]
    print(video_info)

    insertQuery = """
        INSERT INTO processing_videos(id_task, id_video, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)
    """
    runQuery(insertQuery, (task_id, video_info['id'], 'Procesando', datetime.now(), datetime.now()))

    total_duration = original_video.duration
    start_time = 0
    split_counter = 0

    if total_duration <= 20:
        # Procesar el video completo
        processed_video = shorten_video_duration(original_video, 0, total_duration)
        processed_video = add_logo_to_video(processed_video)
        processed_video = resize_video_to_16_9(processed_video)
        processed_video_path = save_processed_video(processed_video, filename)
        insertQuery = """
            INSERT INTO split_videos(id_video, split_path, _order, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)
        """
        runQuery(insertQuery, (video_info['id'], UPLOAD_FOLDER_TO_PROCESSED_VIDEOS + '/' + filename, 1, datetime.now(), datetime.now()))

        # subir al bucket
        upload_to_gcs(processed_video_path, UPLOAD_FOLDER_TO_PROCESSED_VIDEOS + '/' + clip_filename)

    else:
        # Procesar por partes
        for i in range(0, int(total_duration), 20):
            processed_clip = shorten_video_duration(original_video, start_time, start_time + 20)
            processed_clip = add_logo_to_video(processed_clip)
            processed_clip = resize_video_to_16_9(processed_clip)

            # Generate filename with start time
            clip_filename = os.path.splitext(filename)[0] + f'_part_{split_counter}.mp4'

            processed_video_path = save_processed_video(processed_clip, clip_filename)

            # Increment start_time
            start_time += 20
            insertQuery = """
                INSERT INTO split_videos(id_video, split_path, _order, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)
            """
            runQuery(insertQuery, (
            video_info['id'], UPLOAD_FOLDER_TO_PROCESSED_VIDEOS + '/' + clip_filename, split_counter, datetime.now(), datetime.now()))
            split_counter += 1

            # subir al bucket
            upload_to_gcs(processed_video_path, UPLOAD_FOLDER_TO_PROCESSED_VIDEOS + '/' + clip_filename)
    insertQuery = """
        INSERT INTO processing_videos(id_task, id_video, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)
    """
    runQuery(insertQuery, (task_id, video_info['id'], 'Procesado', datetime.now(), datetime.now()))
    os.remove(original_video.filename)
    return True


def insert_video(task_id, url, current_user):

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
        user_id = current_user
        loaded_at = datetime.now()
        processed_at = None
        video_url = url
        task_id = task_id

        runQuery(insert_query,(video_name, path, user_id, duration, loaded_at, processed_at, video_url, task_id))
        # subir al bucket
        upload_to_gcs(file_path, path)
        return video_name
    return None


def runQuery(query, params=None):
    db_params = {
        'dbname': DB_NAME,
        'user': DB_USER,
         'password': DB_PASSWORD,
        'host': DB_HOST,
        'port': DB_PORT
    }

    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    if params:
        cur.execute(query, params)
    else:
        cur.execute(query)

    if cur.description:
        columns = [col[0] for col in cur.description]
        data = [dict(zip(columns, row)) for row in cur.fetchall()]
    else:
        data = None

    conn.commit()

    cur.close()
    conn.close()

    return data


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


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.task(bind=True)
def process_video(self, url, current_user):
    task_id = self.request.id

    if not allowed_file(url):
        error_message = f"El formato del archivo en la URL no está permitido. Se esperaba una extensión de archivo {ALLOWED_EXTENSIONS}"
        return {'error': error_message}

    file_path = insert_video(task_id, url, current_user)
    process_saved_video(task_id, file_path)
    # escribir_archivo()
    return {'status': 'MODIFICADO', 'result': 100}
