# Docker: gestión avanzada y limpieza del entorno (paso 15)

## Ciclo de vida completo con Compose

```
docker compose up -d --build    # construir y levantar en segundo plano
docker compose ps               # estado de los servicios
docker compose stop             # parar sin eliminar
docker compose start            # rearrancar
docker compose down             # parar y eliminar contenedores y red
docker compose down -v          # además elimina los volúmenes nombrados
```

`down` sin `-v` conserva `redis_data` y `backend_data`: al volver a hacer `up` los datos siguen ahí. `down -v` borra también esos volúmenes, perdiendo los reports y el estado de Redis.

## Reconstruir un solo servicio

```
docker compose build backend
docker compose up -d backend
```

Reconstruye y recrea solo el backend; `redis` y `proxy` siguen corriendo intactos. Útil cuando se toca el código de la API sin querer reiniciar toda la infraestructura.

## Escalar el backend

```
docker compose up -d --build --scale backend=3
```

Compose levanta tres réplicas del backend (`docker-infra-backend-1/2/3`), todas en la red interna. NGINX las descubre por el nombre de servicio `backend` vía el DNS interno y reparte las peticiones entre ellas (round-robin del `upstream`). Funciona porque el backend **no publica puerto al host**: si lo publicara, las tres réplicas chocarían por el mismo puerto.

`docker compose ps` tras escalar:

```
NAME                     SERVICE   STATUS
docker-infra-backend-1   backend   Up (healthy)
docker-infra-backend-2   backend   Up (healthy)
docker-infra-backend-3   backend   Up (healthy)
docker-infra-proxy-1     proxy     Up
docker-infra-redis-1     redis     Up (healthy)
```

Verificación de que el proxy llega a un backend cualquiera de las réplicas:

```
docker run --rm --network docker-infra_internal curlimages/curl -sk https://proxy/health
# {"status":"ok"}
```

## Uso de recursos en tiempo real

```
docker stats
```

Snapshot capturado con las tres réplicas activas:

```
NAME                     CPU %     MEM USAGE / LIMIT
docker-infra-backend-1   0.22%     36.36MiB / 3.776GiB
docker-infra-backend-2   0.28%     36.31MiB / 3.776GiB
docker-infra-backend-3   0.23%     36.02MiB / 3.776GiB
docker-infra-proxy-1     0.00%     5.66MiB  / 3.776GiB
docker-infra-redis-1     1.19%     3.83MiB  / 3.776GiB
```

Cada réplica de FastAPI ronda los 36 MB de RAM en reposo; NGINX y Redis apenas consumen unos pocos MB. El límite de memoria mostrado (3.776 GiB) es el de la VM de Docker Desktop sobre WSL2.

## Limpieza y espacio recuperado

Antes de limpiar, `docker system df` muestra qué ocupa espacio y cuánto es recuperable:

```
TYPE            TOTAL   ACTIVE   SIZE       RECLAIMABLE
Images          8       3        766.9MB    369.7MB (48%)
Containers      5       5        942.1kB    0B (0%)
Local Volumes   2       2        0B         0B
Build Cache     20      0        289.8MB    62.22kB
```

Casi la mitad del espacio de imágenes (369.7 MB) es recuperable: son imágenes descargadas para las prácticas (`hello-world`, `ubuntu:22.04`, `curlimages/curl`, etc.) que ningún contenedor en marcha usa. Los volúmenes y los contenedores activos no son recuperables porque están en uso.

Comandos de limpieza, de menos a más agresivo:

```
docker builder prune -f     # solo caché de build sin usar
docker image prune -f       # solo imágenes "dangling" (sin tag)
docker system prune -a      # TODO lo no usado: imágenes sin contenedor, redes, caché
```

`docker builder prune -f` recuperó la caché de build huérfana (62 kB en este caso, porque casi toda seguía referenciada). `docker system prune -a` recuperaría los ~370 MB de imágenes inactivas que reporta `system df`; no se ejecuta aquí para no borrar imágenes base que sirven a otras prácticas, pero el comando es el que se usaría en un servidor real para recuperar espacio.

Cuidado con `docker system prune -a`: elimina toda imagen que no tenga un contenedor asociado, no solo las de este proyecto. Las imágenes de servicios que estén corriendo quedan protegidas; las paradas no.
