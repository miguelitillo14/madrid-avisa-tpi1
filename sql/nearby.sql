-- Avisos diferentes situados a menos de 50 m. ST_DWithin usa el índice GiST.
SELECT a.id AS aviso_a, b.id AS aviso_b,
       a.categoria1 AS categoria_a, b.categoria1 AS categoria_b,
       round(ST_Distance(a.geom, b.geom)::numeric, 1) AS distancia_m,
       a.distrito, a.barrio
FROM aviso AS a
JOIN aviso AS b ON b.id > a.id
                AND ST_DWithin(a.geom, b.geom, 50)
ORDER BY distancia_m, aviso_a, aviso_b;
