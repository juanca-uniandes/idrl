import psycopg2
import os
from google.cloud import storage

BUCKET_NAME = "misoe3g23"
CREDENTIALS_FILE = "credentials-cuenta-storage.json"
DB_NAME = "idrl_db"
DB_USER = "idrl_user"
DB_PASSWORD = "idrl_2024"
DB_HOST = "161.132.40.204"
DB_PORT = 5433

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_FILE

def upload_to_gcs(source_file_path, destination_blob_name):
  storage_client = storage.Client.from_service_account_json(CREDENTIALS_FILE)
  bucket = storage_client.bucket(BUCKET_NAME)

  # Upload the file to the bucket
  blob = bucket.blob(destination_blob_name)
  blob.upload_from_filename(source_file_path)

  print(f"File {source_file_path} uploaded to gs://{BUCKET_NAME}/{destination_blob_name}")


# Función para conectarse a la base de datos y ejecutar el status de una tarea
def fn_info_task(id_task):
    db_params = {
        'dbname': DB_NAME,
        'user': DB_USER,
        'password': DB_PASSWORD,
        'host': DB_HOST,
        'port': DB_PORT
    }
    try:
        # Conexión a la base de datos PostgreSQL
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        # Ejecutar el procedimiento almacenado
        query = """select * from fn_info_task(%s);"""
        cur.execute(query, (id_task,))

        # Obtener los resultados del procedimiento almacenado
        results = cur.fetchall()

        # Cerrar cursor y conexión
        cur.close()
        conn.close()

        return results

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return None