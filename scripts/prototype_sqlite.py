"""TPI 1: caso práctico con avisos ciudadanos reales del Ayuntamiento de Madrid.

Fixture: primeros cinco registros de 2026 del recurso municipal 212411-17.
Coordenadas reales UTM-30 ETRS89 (metros), tomadas de la API CKAN municipal.
Prototipo ejecutado con SQLite R-tree y una UDF Euclídea para ST_DWithin_m.
No requiere PostGIS; el SQL PostGIS equivalente se incluye en el TPI.
"""
import sqlite3
import csv
from pathlib import Path

con=sqlite3.connect(':memory:')
def dwithin_m(x1,y1,x2,y2,limit):
    dx=x1-x2; dy=y1-y2
    return int(dx*dx+dy*dy <= limit*limit)
con.create_function('ST_DWITHIN_M',5,dwithin_m,deterministic=True)
con.executescript('''
CREATE TABLE aviso(
  id INTEGER PRIMARY KEY,
  tipo TEXT NOT NULL,
  categoria1 TEXT,
  categoria2 TEXT,
  distrito TEXT,
  barrio TEXT,
  fecha TEXT,
  calle TEXT,
  portal TEXT,
  x REAL NOT NULL,
  y REAL NOT NULL
);
CREATE VIRTUAL TABLE aviso_rtree USING rtree(id,min_x,max_x,min_y,max_y);
''')
# Five real records saved from the municipal CKAN API response.
fixture=Path(__file__).resolve().parents[1] / 'data' / 'avisos_madrid_muestra_2026.csv'
with fixture.open(encoding='utf-8-sig',newline='') as stream:
    source=list(csv.DictReader(stream))
rows=[]
for r in source:
    rows.append((int(r['_id']),r['TIPO_INCIDENCIA'],r['CATEGORIA_NIVEL1'],
      r['CATEGORIA_NIVEL2'],r['DISTRITO'],r['BARRIO'],r['FECHA_DE_RECEPCION'],
      f"{r['TIPO_VIAL']} {r['NOMBRE_DE_VIAL']}",r['NUMERO'],
      float(r['COORDENADA_REAL_X']),float(r['COORDENADA_REAL_Y'])))
con.executemany('INSERT INTO aviso VALUES (?,?,?,?,?,?,?,?,?,?,?)',rows)
con.executemany('INSERT INTO aviso_rtree VALUES (?,?,?,?,?)',[(r[0],r[-2],r[-2],r[-1],r[-1]) for r in rows])
radius=50
sql='''SELECT a.id,b.id,a.categoria1,b.categoria1,
       sqrt((a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y)) AS distancia_m
FROM aviso_rtree ra JOIN aviso a ON a.id=ra.id
JOIN aviso_rtree rb ON rb.id>a.id
 AND rb.min_x<=ra.max_x+? AND rb.max_x>=ra.min_x-?
 AND rb.min_y<=ra.max_y+? AND rb.max_y>=ra.min_y-?
JOIN aviso b ON b.id=rb.id
WHERE ST_DWITHIN_M(a.x,a.y,b.x,b.y,?)=1
ORDER BY distancia_m,a.id,b.id'''
print('Fuente: CSV con los primeros 5 registros del recurso municipal 212411-17 (avisos recibidos SIC), 2026.')
print('CRS declarado en el diccionario municipal: UTM-30 / ETRS89; análisis de coordenada REAL; unidades m.')
print('Registros cargados:',con.execute('SELECT count(*) FROM aviso').fetchone()[0])
print('Pares de avisos distintos a 50 m o menos:')
results=con.execute(sql,(radius,)*5).fetchall()
if results:
 for a,b,ca,cb,dist in results:
  print(f'{a} | {b} | {dist:.1f} m | {ca} / {cb}')
else: print('ninguno')
print('Pares dentro del umbral:',len(results))
print('Avisos indexados en R-tree:',con.execute('SELECT count(*) FROM aviso_rtree').fetchone()[0])
print('Plan de consulta:')
for r in con.execute('EXPLAIN QUERY PLAN '+sql,(radius,)*5): print(r[3])
