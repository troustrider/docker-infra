# docker-infra

Dockerización del [toolkit de sysadmin en Python](../sysadmin-toolkit) de la fase anterior. Tres servicios orquestados con Docker Compose: una API en FastAPI, Redis como caché y almacén de IPs sospechosas, y NGINX como proxy inverso con HTTPS local y rate limiting. El backend nunca es accesible directamente desde fuera, solo a través de NGINX.

## Arquitectura

```
                    ┌─────────────┐
   cliente ───────► │    NGINX    │  puertos 80 (redirige) / 443
                    │   (proxy)   │
                    └──────┬──────┘
                           │ red interna "internal" (bridge)
                    ┌──────▼──────┐       ┌─────────┐
                    │   backend   │ ────► │  redis  │
                    │  (FastAPI)  │       │         │
                    └─────────────┘       └─────────┘
```

- `backend` y `redis` no publican ningún puerto al host. Solo `proxy` lo hace.
- `backend_data` (volumen) persiste los reports aunque se recree el contenedor.
- `redis_data` (volumen) persiste la caché y el set de IPs sospechosas.
- `./nginx.conf` y `./certs` se montan como bind mounts de solo lectura.

## Arrancar el stack

1. Generar el certificado autofirmado (instrucciones en [`certs/README.md`](certs/README.md)).
2. Copiar `.env.example` a `.env` y ajustar `REDIS_PASSWORD` si quieres.
3. Levantar todo:

```bash
docker compose up -d --build
```

4. Probar:

```bash
curl -k https://localhost/health
curl -k https://localhost/logs/summary
curl -k -X POST https://localhost/threats/192.168.1.100
curl -k https://localhost/threats
```

El navegador avisará de certificado no confiable porque es autofirmado, es lo esperado en local.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/health` | Healthcheck simple |
| GET | `/inventory` | Inventario completo (CSV de la fase 7) |
| GET | `/inventory/vulnerable` | Hosts con Windows Server o menos de 4GB RAM |
| POST | `/reports` | Guarda un report `{host, message}` en el volumen `backend_data` |
| GET | `/reports` | Lista los reports persistidos |
| GET | `/logs/summary` | Parsea `auth.log` y cachea el resultado en Redis 60s |
| POST | `/threats/{ip}` | Añade una IP al SET de Redis `suspicious_ips` |
| GET | `/threats` | Lista las IPs sospechosas reportadas |

## Comandos útiles

```bash
docker compose ps                          # estado de los servicios
docker compose logs -f backend             # logs en vivo de un servicio
docker compose build backend && docker compose up -d backend   # rebuild selectivo
docker compose up -d --scale backend=3     # escalar el backend
docker stats                               # uso de recursos en tiempo real
docker exec -it docker-infra-redis-1 redis-cli -a $REDIS_PASSWORD   # entrar a Redis
docker system prune -a                     # limpiar imágenes/contenedores no usados
```

## Documentación técnica

- [`docs/docker-teoria.md`](docs/docker-teoria.md) — VM vs contenedor, ciclo de vida
- [`docs/docker-primeros-pasos.md`](docs/docker-primeros-pasos.md) / [`docs/docker-cli-esencial.md`](docs/docker-cli-esencial.md) — CLI de Docker
- [`docs/docker-imagenes-capas.md`](docs/docker-imagenes-capas.md) — Dockerfile, capas, caché de build, tamaño e history de la imagen propia
- [`docs/docker-redes-volumenes.md`](docs/docker-redes-volumenes.md) — redes bridge/host/none, volúmenes vs bind mounts
- [`docs/nginx-proxy-inverso.md`](docs/nginx-proxy-inverso.md) — proxy inverso, upstream/server, HTTPS, rate limiting
- [`docs/docker-gestion-limpieza.md`](docs/docker-gestion-limpieza.md) — ciclo de vida con Compose, escalado, `docker stats`, limpieza y espacio recuperado
