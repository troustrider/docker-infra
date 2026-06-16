![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![NGINX](https://img.shields.io/badge/NGINX-009639?style=for-the-badge&logo=nginx&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

# 🐳 Docker Infra
> Infraestructura inmutable: API dockerizada tras un proxy inverso NGINX

Dockerización del [toolkit de sysadmin en Python](https://github.com/troustrider/python-sysadmin-toolkit) de la fase anterior. Tres servicios orquestados con Docker Compose: una API en FastAPI, Redis como caché y almacén de IPs sospechosas, y NGINX como proxy inverso con HTTPS local y rate limiting. El backend nunca es accesible directamente desde fuera, solo a través de NGINX. Arranca con un solo comando.

---

## Características

- Stack de tres servicios levantado con un único `docker compose up`
- API FastAPI dockerizada sobre imagen `python:3.11-alpine` (151 MB)
- Backend y Redis aislados en una red bridge interna, sin publicar puertos al host
- NGINX como único punto de entrada: redirige HTTP a HTTPS y aplica rate limiting
- HTTPS local con certificado autofirmado y servido de archivos estáticos
- Persistencia con volúmenes nombrados para los reports y los datos de Redis
- Healthchecks encadenados: el backend espera a Redis y el proxy al backend
- Secretos fuera del código vía `.env` (ignorado por Git)

---

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

---

## Tecnologías

| Servicio | Imagen | Uso |
|----------|--------|-----|
| backend | `python:3.11-alpine` + FastAPI | API REST de inventario, logs y amenazas |
| redis | `redis:7-alpine` | Caché del parseo de logs y SET de IPs sospechosas |
| proxy | `nginx:1.27-alpine` | Proxy inverso, HTTPS, rate limiting, estáticos |

| Auxiliares | Uso |
|------------|-----|
| Docker Compose v2 | Orquestación de los tres servicios |
| Volúmenes nombrados | Persistencia de reports y datos de Redis |
| Red bridge interna | Aislamiento y service discovery por nombre |
| OpenSSL | Certificado autofirmado para HTTPS local |

---

## Estructura del proyecto

```
docker-infra/
├── Dockerfile              # imagen del backend (alpine, caché de capas)
├── docker-compose.yml      # backend + redis + proxy, red, volúmenes, healthchecks
├── nginx.conf              # upstream, redirect HTTPS, rate limiting, estáticos
├── .dockerignore           # excluye docs, .git, __pycache__ y .env del build
├── .env.example            # plantilla de variables (REDIS_PASSWORD)
├── app/
│   ├── main.py             # API FastAPI
│   ├── requirements.txt
│   ├── auth.log            # log SSH de ejemplo
│   └── inventory.csv       # inventario de la fase 7
├── certs/                  # certificados autofirmados (no versionados)
│   └── README.md
├── static/
│   └── index.html          # archivo servido directamente por NGINX
└── docs/                   # documentación técnica de la fase
```

---

## Despliegue

```bash
git clone https://github.com/troustrider/docker-infra.git
cd docker-infra

# 1. Generar el certificado autofirmado (ver certs/README.md)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/selfsigned.key -out certs/selfsigned.crt -subj "/CN=localhost"

# 2. Copiar la plantilla de entorno y ajustar la contraseña
cp .env.example .env

# 3. Levantar todo el stack
docker compose up -d --build
```

Probar (el navegador avisará de certificado no confiable porque es autofirmado, es lo esperado en local):

```bash
curl -k https://localhost/health
curl -k https://localhost/logs/summary
curl -k -X POST https://localhost/threats/192.168.1.100
curl -k https://localhost/threats
```

---

## Endpoints

| Método | Ruta | Qué hace |
|--------|------|----------|
| GET | `/health` | Healthcheck simple |
| GET | `/inventory` | Inventario completo (CSV de la fase 7) |
| GET | `/inventory/vulnerable` | Hosts con Windows Server o menos de 4 GB RAM |
| POST | `/reports` | Guarda un report `{host, message}` en el volumen `backend_data` |
| GET | `/reports` | Lista los reports persistidos |
| GET | `/logs/summary` | Parsea `auth.log` y cachea el resultado en Redis 60 s |
| POST | `/threats/{ip}` | Añade una IP al SET de Redis `suspicious_ips` |
| GET | `/threats` | Lista las IPs sospechosas reportadas |

---

## Documentación técnica

- [`docs/docker-teoria.md`](docs/docker-teoria.md) — VM vs contenedor, ciclo de vida
- [`docs/docker-primeros-pasos.md`](docs/docker-primeros-pasos.md) / [`docs/docker-cli-esencial.md`](docs/docker-cli-esencial.md) — CLI de Docker
- [`docs/docker-imagenes-capas.md`](docs/docker-imagenes-capas.md) — Dockerfile, capas, caché de build, tamaño e history
- [`docs/docker-redes-volumenes.md`](docs/docker-redes-volumenes.md) — redes bridge/host/none, volúmenes vs bind mounts
- [`docs/nginx-proxy-inverso.md`](docs/nginx-proxy-inverso.md) — proxy inverso, upstream/server, HTTPS, rate limiting
- [`docs/docker-gestion-limpieza.md`](docs/docker-gestion-limpieza.md) — ciclo de vida, escalado, `docker stats`, limpieza

---

*Desarrollado durante las prácticas en [Corner Estudios](https://www.corner-estudios.com) — Karim Abatouy — 2026*
