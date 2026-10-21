CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS aviso (
    id BIGINT PRIMARY KEY,
    tipo TEXT NOT NULL,
    categoria1 TEXT,
    categoria2 TEXT,
    canal TEXT,
    fecha_recepcion DATE NOT NULL,
    distrito TEXT,
    barrio TEXT,
    calle TEXT,
    portal TEXT,
    geom geometry(Point, 25830)
);
CREATE INDEX IF NOT EXISTS aviso_geom_gist ON aviso USING GIST (geom);
CREATE INDEX IF NOT EXISTS aviso_fecha_idx ON aviso (fecha_recepcion);
CREATE INDEX IF NOT EXISTS aviso_categoria_fecha_idx ON aviso (categoria1, fecha_recepcion);
