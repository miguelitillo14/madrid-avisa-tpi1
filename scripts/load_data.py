import argparse
import csv
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from influxdb_client import InfluxDBClient, Point, WritePrecision
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
from influxdb_client.client.write_api import SYNCHRONOUS


def parse_date(value: str):
    return datetime.strptime(value, "%d/%m/%Y").date()


def load_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def main():
    parser = argparse.ArgumentParser(description="Carga el CSV de avisos en PostGIS e InfluxDB.")
    parser.add_argument("--csv", type=Path, default=Path("data/avisos_madrid_muestra_2026.csv"))
    args = parser.parse_args()
    rows = load_csv(args.csv)
    if not rows:
        raise SystemExit("El CSV no contiene avisos.")

    dsn = os.getenv("POSTGRES_DSN", "postgresql://avisos:avisos_local@localhost:5432/avisos")
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for row in rows:
                date_value = parse_date(row["FECHA_DE_RECEPCION"])
                x, y = float(row["COORDENADA_REAL_X"]), float(row["COORDENADA_REAL_Y"])
                cur.execute("""
                    INSERT INTO aviso (id,tipo,categoria1,categoria2,canal,fecha_recepcion,
                                       distrito,barrio,calle,portal,geom)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            ST_SetSRID(ST_MakePoint(%s,%s),25830))
                    ON CONFLICT (id) DO UPDATE SET
                      tipo=EXCLUDED.tipo, categoria1=EXCLUDED.categoria1,
                      categoria2=EXCLUDED.categoria2, canal=EXCLUDED.canal,
                      fecha_recepcion=EXCLUDED.fecha_recepcion, distrito=EXCLUDED.distrito,
                      barrio=EXCLUDED.barrio, calle=EXCLUDED.calle, portal=EXCLUDED.portal,
                      geom=EXCLUDED.geom
                """, (int(row["_id"]), row["TIPO_INCIDENCIA"], row["CATEGORIA_NIVEL1"],
                      row["CATEGORIA_NIVEL2"], row["CANAL_DE_ENTRADA"], date_value,
                      row["DISTRITO"], row["BARRIO"],
                      f"{row['TIPO_VIAL']} {row['NOMBRE_DE_VIAL']}", row["NUMERO"], x, y))

    counts = Counter((parse_date(r["FECHA_DE_RECEPCION"]), r["DISTRITO"], r["CATEGORIA_NIVEL1"]) for r in rows)
    token = os.getenv("INFLUX_TOKEN", "madrid_avisa_local_token")
    org = os.getenv("INFLUX_ORG", "madrid")
    bucket = os.getenv("INFLUX_BUCKET", "avisos")
    url = os.getenv("INFLUX_URL", "http://localhost:8086")
    with InfluxDBClient(url=url, token=token, org=org) as client:
        writer = client.write_api(write_options=SYNCHRONOUS)
        points = [Point("avisos_diarios")
                  .tag("distrito", district or "sin_dato")
                  .tag("categoria", category or "sin_dato")
                  .field("total", int(total))
                  .time(datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc), WritePrecision.S)
                  for (day, district, category), total in counts.items()]
        writer.write(bucket=bucket, org=org, record=points)
    print(f"CSV: {args.csv}; filas leídas: {len(rows)}")
    print("PostGIS: avisos cargados (SRID 25830) con geometría e índice GiST.")
    print(f"InfluxDB: {len(points)} puntos diarios agregados por fecha, distrito y categoría.")
    print("Repetir la carga actualiza los avisos y sobrescribe las mismas series temporales.")


if __name__ == "__main__":
    main()
