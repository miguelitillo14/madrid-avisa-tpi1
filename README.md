# Proyecto TPI 1 — avisos ciudadanos de Madrid

Proyecto práctico de bases de datos especializadas sobre el conjunto municipal **Avisos ciudadanos recibidos (SIC)**. PostGIS conserva cada aviso y su ubicación proyectada; InfluxDB guarda agregados diarios por distrito y categoría. Así se pueden responder dos preguntas operativas: qué incidencias ocurren cerca unas de otras y cómo cambia su volumen con el tiempo.

## Datos y atribución

El CSV incluido contiene cinco filas reales del recurso municipal de 2026, con atribución al Ayuntamiento de Madrid. Las coordenadas `COORDENADA_REAL_X/Y` están en UTM-30 / ETRS89 (EPSG:25830), por lo que las distancias se expresan en metros. Fuente y licencia: [datos.madrid.es — Madrid Avisa](https://datos.madrid.es/dataset/212411-0-madrid-avisa), CC BY 4.0. Fecha del extracto: 1 de enero de 2026. La muestra breve permite reproducir el caso descrito en la memoria; para un análisis representativo, descarga el CSV completo actualizado desde el portal y pásalo con `--csv ruta/al/archivo.csv`.

## Arranque local

Requisitos: Docker con Compose, Python 3.10 o superior.

```powershell
Copy-Item .env.example .env
 docker compose up -d
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/load_data.py
```

La primera inicialización crea el esquema PostGIS y las extensiones. Para comprobar el resultado espacial:

```powershell
docker compose exec postgis psql -U avisos -d avisos -f /workspace/sql/nearby.sql
``` En InfluxDB, abre `http://localhost:8086`, inicia sesión con los valores locales de `.env.example` y consulta el bucket `avisos`.

La carga es idempotente: PostGIS usa `ON CONFLICT` por id y las escrituras temporales repiten la misma clave de serie y marca temporal. Los datos de acceso del ejemplo solo son para desarrollo local; no se deben reutilizar en un servidor público.

## Archivos

- `main.tex`: memoria TPI en LaTeX.
- `docker-compose.yml`: PostGIS e InfluxDB locales.
- `sql/schema.sql`: tabla espacial e índices.
- `sql/nearby.sql`: consulta de proximidad con `ST_DWithin`.
- `scripts/load_data.py`: ETL CSV → PostGIS + InfluxDB.
- `scripts/prototype_sqlite.py`: demostración ejecutable del resultado de proximidad con R-tree para el conjunto de cinco filas.
- `data/avisos_madrid_muestra_2026.csv`: muestra real reproducible.

## Estado de verificación

La consulta de proximidad sí se ejecutó en SQLite con R-tree sobre la muestra real: encontró un único par a menos de 50 m, con distancia de 21,0 m. En este equipo no estaba iniciado Docker, por lo que la pila PostGIS/InfluxDB se entrega configurada pero no se afirma que se haya ejecutado aquí. Al levantarla en un equipo con Docker, vuelve a ejecutar la carga y la consulta para validar ambos motores.
