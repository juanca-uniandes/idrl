import os
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

# Obtener las variables de entorno
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")

# Conexión a la base de datos
connection = psycopg2.connect(
    dbname="idrl_db",
    user="idrl_user",
    password="idrl_2024",
    host="postgres"
)

# Crear un cursor para ejecutar comandos SQL
cursor = connection.cursor()

password = generate_password_hash('12345')

# Definir sentencias SQL para crear tablas
create_tables_query = """
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE,
    pass VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    video_name VARCHAR(255),
    path VARCHAR(255),
    user_id INTEGER REFERENCES usuarios(id),
    duration BIGINT,
    loaded_at TIMESTAMP,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    url VARCHAR(255), 
    task_id VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS processing_videos (
    id SERIAL PRIMARY KEY,
    id_task VARCHAR(100),
    id_video INTEGER,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS split_videos (
    id SERIAL PRIMARY KEY,
    id_video INTEGER REFERENCES videos(id),  -- Cambiado el tipo de dato a INTEGER
    split_path VARCHAR(255),
    _order INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
--------------------------------------------------------------
--Usuario de prueba

INSERT INTO public.usuarios (username, email, pass, created_at, updated_at)
VALUES ('usuario1', 'admin@gmail.com', %s, '2024-04-10', '2024-04-10')
ON CONFLICT (username)
DO UPDATE SET
    email = EXCLUDED.email,
    pass = EXCLUDED.pass,
    updated_at = EXCLUDED.updated_at;
--------------------------------------------------------------
--procedimiento para la consulta de todas de tareas
CREATE OR REPLACE FUNCTION fn_info_tasks(max_limit INT, orden INT)
RETURNS TABLE (
	task_id VARCHAR(100)
	, status VARCHAR(20)
)
language plpgsql 
AS $$
BEGIN
    RETURN QUERY 
		SELECT pv.id_task, pv.status 
		FROM processing_videos pv
		ORDER BY
		    CASE
		        WHEN orden = 0 THEN pv.id_task
		    END ASC,
		    CASE
		        WHEN orden = 1  THEN pv.id_task
		    END desc
		LIMIT case when (max_limit is not null or max_limit > 0) then max_limit end;
END
$$;

--procedimiento para la consulta de una tarea
CREATE OR replace FUNCTION fn_info_task(_task_id VARCHAR(100))
RETURNS TABLE (
	  id_task VARCHAR(100)
	, status VARCHAR(20)
	, url  VARCHAR(255)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY 
		SELECT pv.id_task, pv.status, v.url
		FROM processing_videos pv
			left join videos v on v.id = pv.id_video 
		where  pv.id_task = _task_id;
END
$$;

--procedimiento para recuperar el path del video
CREATE OR replace FUNCTION fn_task_video_path(_task_id VARCHAR(100))
RETURNS TABLE (
	  path_video VARCHAR(255)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY 
		SELECT v."path" as path_video
		FROM processing_videos pv
			join videos v on v.id = pv.id_video  
		where  pv.id_task = _task_id;
END
$$;

--procedimiento para recuperar el path de los splits
CREATE OR replace FUNCTION fn_task_split_video_path(_task_id VARCHAR(100))
RETURNS TABLE (
	  path_video VARCHAR(255)
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY 
		SELECT v.split_path as path_video
		FROM processing_videos pv
			join split_videos v on v.id_video   = pv.id_video  
		where  pv.id_task =  _task_id;
END
$$;

--procedimiento para abortar tarea
CREATE OR REPLACE PROCEDURE sp_abort_task(_id_task VARCHAR(100))
LANGUAGE plpgsql
AS $$
	declare _id_video INT;
begin
--Recuperar id del video
	SELECT pv.id_video 
	FROM processing_videos pv
	where  pv.id_task = _id_task
	into _id_video;

--borrar split_videos
	delete from split_videos
	where id_video = _id_video;

--borrar video
	delete from videos
	where id = _id_video;

--Actualizar procesamiento
	update processing_videos 
	set status = 'canceled'
	where id_task = _id_task;
END
$$;
"""

# Ejecutar las sentencias SQL
cursor.execute(create_tables_query, (password,))

# Confirmar los cambios
connection.commit()

# Cerrar la conexión y el cursor
cursor.close()
connection.close()
