-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id   SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL
);

-- Tabla de eventos
CREATE TABLE IF NOT EXISTS eventos (
    id     SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    fecha  DATE NOT NULL,
    lugar  VARCHAR(200) NOT NULL
);

-- Tabla de tickets
CREATE TABLE IF NOT EXISTS tickets (
    id               SERIAL PRIMARY KEY,
    evento_id        INTEGER NOT NULL REFERENCES eventos(id),
    usuario_id       INTEGER REFERENCES usuarios(id),
    estado           VARCHAR(20) NOT NULL DEFAULT 'disponible'
                         CHECK (estado IN ('disponible', 'reservado', 'confirmado')),
    fecha_expiracion TIMESTAMP
);

-- Datos de prueba: usuarios
INSERT INTO usuarios (nombre) VALUES
    ('Ana García'),
    ('Carlos López'),
    ('María Martínez');

-- Datos de prueba: eventos
INSERT INTO eventos (nombre, fecha, lugar) VALUES
    ('Concierto de Rock', '2026-05-10', 'Estadio Nacional'),
    ('Festival de Jazz', '2026-06-15', 'Parque Central'),
    ('Obra de Teatro', '2026-07-20', 'Teatro Municipal');

-- Datos de prueba: tickets (10 por evento)
INSERT INTO tickets (evento_id, estado)
SELECT e.id, 'disponible'
FROM eventos e
CROSS JOIN generate_series(1, 10);
