import psycopg2
import os

# Función para conectarse a la base de datos y ejecutar el status de todas las tareas
def fn_info_tasks(max, order):
    db_params = {
        'dbname': "idrl_db",
        'user': "idrl_user",
        'password': "idrl_2024",
        'host': "161.132.40.204",
        'port': "5433"
  	 }
    try:
        # Conexión a la base de datos PostgreSQL
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        # Ejecutar el procedimiento almacenado
        cur.execute('select * from fn_info_tasks(%s, %s);', (max, order) )

        # Obtener los resultados del procedimiento almacenado
        results = cur.fetchall()

        # Cerrar cursor y conexión
        cur.close()
        conn.close()

        return results

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return None

# Función para conectarse a la base de datos y ejecutar el status de una tarea
def fn_info_task(id_task):
    db_params = {
        'dbname': "idrl_db",
        'user': "idrl_user",
        'password': "idrl_2024",
        'host': "161.132.40.204",
        'port': "5433"
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

def fn_path_video(id_task):
    db_params = {
        'dbname': "idrl_db",
        'user': "idrl_user",
        'password': "idrl_2024",
        'host': "161.132.40.204",
        'port': "5433"
    }
    try:
        # Conexión a la base de datos PostgreSQL
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        # Ejecutar el procedimiento almacenado        
        query = """select * from fn_task_video_path(%s);"""
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

def fn_path_split_video(id_task):
    db_params = {
        'dbname': "idrl_db",
        'user': "idrl_user",
        'password': "idrl_2024",
        'host': "161.132.40.204",
        'port': "5433"
    }
    try:
        # Conexión a la base de datos PostgreSQL
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        # Ejecutar el procedimiento almacenado        
        query = """select * from fn_task_split_video_path(%s);"""
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

def sp_abort_task(id_task):
    db_params = {
        'dbname': "idrl_db",
        'user': "idrl_user",
        'password': "idrl_2024",
        'host': "postgres"
    }
    try:
        # Conexión a la base de datos PostgreSQL
        conn = psycopg2.connect(**db_params)
        cur = conn.cursor()

        # Ejecutar el procedimiento almacenado        
        query = "CALL sp_abort_task(%s);"
        cur.execute(query, (id_task,))

        # commit the transaction
        conn.commit()
        
        # Obtener los resultados del procedimiento almacenado
        results = cur.fetchall()

        # Cerrar cursor y conexión
        cur.close()
        conn.close()

        return results

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return None

def delete_task(id_task):
    path_videos = fn_path_video(id_task)

    for file in path_videos:               
        if os.path.exists(file[0]):
            os.remove(file[0])
    
    path_split_videos = fn_path_split_video(id_task)
    for file in path_split_videos:
        if os.path.exists(file[0]):
            os.remove(file[0])
    
    return sp_abort_task(id_task)
