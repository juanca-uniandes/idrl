import os
import psycopg2

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

# Definir sentencias SQL para crear tablas
create_tables_query = """
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255),
    email VARCHAR(255),
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
    id_queue BIGINT,
    id_video INTEGER REFERENCES videos(id),  -- Cambiado el tipo de dato a INTEGER
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
INSERT INTO public.usuarios
(username, email, pass, created_at, updated_at)
VALUES('usuario1', 'usuario1@gmail.com', '12345', '2024-04-10', '2024-04-10');
"""

# Ejecutar las sentencias SQL
cursor.execute(create_tables_query)

# Confirmar los cambios
connection.commit()

# Cerrar la conexión y el cursor
cursor.close()
connection.close()
