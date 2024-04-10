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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
