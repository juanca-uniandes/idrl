# tasks.py
from celery import Celery
import time
import os
import psycopg2
from datetime import datetime

broker_url = 'redis://redis:6379/0'
app = Celery('tasks', backend='rpc://', broker=broker_url)

# Obtener las variables de entorno
DB_NAME = 'idrl_db'#os.getenv("POSTGRES_DB_NAME")
DB_USER = 'idrl_user'#os.getenv("POSTGRES_DB_USER")
DB_PASSWORD = 'idrl_2024' #os.getenv("POSTGRES_DB_PASSWORD")
DB_HOST = 'postgres_db' #os.getenv("POSTGRES_HOST")
DB_PORT = 5432

def insert_video():
    # Conexión a la base de datos 'idrl_db'
    db_params = {
        'dbname': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'host': DB_HOST,  # Nombre del contenedor de PostgreSQL
        'port': DB_PORT
    }

    # Create a cursor object
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    # Insert a record into the videos table
    insert_query = """
        INSERT INTO videos (video_name, path, user_id, duration, loaded_at, processed_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    video_name = "example_video.mp4"
    path = "/path/to/video/example_video.mp4"
    user_id = 1  # Assuming user_id is 1
    duration = 3600  # Duration in seconds
    loaded_at = datetime.now()
    processed_at = None  # Assuming the video is not processed yet    

    # Execute the insert query
    cur.execute(insert_query, (video_name, path, user_id, duration, loaded_at, processed_at))

    # Commit the transaction
    conn.commit()

    # Close cursor and connection
    cur.close()
    conn.close()

def insert_split_video(order_video):
    # Conexión a la base de datos 'idrl_db'
    db_params = {
        'dbname': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'host': DB_HOST,  # Nombre del contenedor de PostgreSQL
        'port': DB_PORT
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
    insert_video()
    for i in range(1, 6):
        insert_split_video(i)
        time.sleep(20)
        self.update_state(state='PROGRESS', meta={'progress': i*20})
    #Actualizar estado de la tarea
    return {'status': 'completado!', 'result': 100}