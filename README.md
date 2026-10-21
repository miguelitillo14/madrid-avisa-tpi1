# Proyecto TPI 1 — avisos ciudadanos de Madrid

Proyecto práctico de bases de datos especializadas sobre el conjunto municipal **Avisos ciudadanos recibidos (SIC)**. PostGIS conserva los avisos y sus ubicaciones; InfluxDB guarda agregados diarios por distrito y categoría para analizar la evolución temporal.

## Datos y atribución

El CSV incluido contiene cinco filas reales del recurso municipal de 2026, con atribución al Ayuntamiento de Madrid. Las coordenadas `COORDENADA_REAL_X/Y` están en UTM-30 / ETRS89 (EPSG:25830), por lo que las distancias se expresan en metros. Fuente y licencia: [datos.madrid.es — Madrid Avisa](https://datos.madrid.es/dataset/212411-0-madrid-avisa), CC BY 4.0. Fecha del extracto: 1 de enero de 2026. Para un análisis más representativo, descarga el CSV completo actualizado desde el portal y pásalo con `--csv ruta/al/archivo.csv`.

## Arranque local

Requisitos: Docker con Compose y Python 3.10 o superior.

```powershell
Copy-Item .env.example .env
docker compose up -d
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/load_data.py
```

La primera inicialización crea el esquema PostGIS y sus índices. La consulta espacial se ejecuta así:

```powershell
docker compose exec postgis psql -U avisos -d avisos -f /workspace/sql/nearby.sql
```

Para consultar InfluxDB, abre `http://localhost:8086` e inicia sesión con los valores de desarrollo de `.env.example`. El ejemplo de Flux está en `sql/serie_diaria.flux`; cubre los últimos 365 días para incluir la fecha de la muestra.

La carga es idempotente: PostGIS usa `ON CONFLICT` por identificador y las escrituras temporales repiten la misma serie y marca de tiempo. Las credenciales del ejemplo son únicamente para desarrollo local y no deben reutilizarse en un servidor público.

## Archivos

- `main.tex`: memoria TPI en LaTeX.
- `docker-compose.yml`: PostGIS e InfluxDB locales.
- `sql/schema.sql`: tabla espacial e índices.
- `sql/nearby.sql`: consulta de proximidad con `ST_DWithin`.
- `sql/serie_diaria.flux`: consulta temporal.
- `scripts/load_data.py`: ETL CSV → PostGIS + InfluxDB.
- `scripts/prototype_sqlite.py`: demostración con R-tree para la muestra de cinco filas.
- `data/avisos_madrid_muestra_2026.csv`: muestra real reproducible.

## Verificación realizada

Probado con Docker Engine 29.9.1, PostGIS 16-3.4 e InfluxDB 2.7. El cargador insertó cinco avisos con SRID 25830 y escribió cinco puntos diarios en InfluxDB. Se repitió la carga: PostGIS mantuvo cinco IDs únicos e InfluxDB siguió devolviendo cinco agregados, sin duplicados. La consulta PostGIS devolvió un único par: avisos 2 y 4, del barrio Media Legua, con distancia de **21,0 m**; la consulta Flux devolvió cinco grupos, uno por combinación de distrito y categoría, con total 1 cada uno. La misma proximidad se había comprobado también con SQLite/R-tree. La muestra cubre un solo día, de modo que no permite evaluar tendencias temporales.
