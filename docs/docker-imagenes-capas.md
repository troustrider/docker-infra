# Docker: imágenes por capas y el Dockerfile

## Sistema de capas

Una imagen Docker no es un archivo monolítico. Es una pila de capas de solo lectura apiladas unas sobre otras. Cada instrucción `RUN`, `COPY` o `ADD` del Dockerfile genera una nueva capa que contiene únicamente los cambios introducidos respecto a la capa anterior. Docker usa OverlayFS para presentar todas esas capas como un único sistema de archivos coherente.

Cuando se construye una imagen, Docker calcula un hash para cada capa. Si la capa no ha cambiado desde el último build, la reutiliza desde la caché en lugar de recalcularla. Esto es lo que se llama **caché de capas**.

El orden de las instrucciones afecta directamente al rendimiento del build porque la caché se invalida en cascada: si una capa cambia, todas las capas posteriores se reconstruyen aunque su contenido no haya variado. Por eso las instrucciones que cambian con frecuencia (copiar el código fuente) deben ir al final, y las que cambian poco (instalar dependencias) deben ir antes.

Ejemplo del impacto del orden:

```
# Mal orden — si cambia main.py se reinstalan todas las dependencias
COPY . .
RUN pip install -r requirements.txt

# Orden correcto — si cambia main.py, pip install se sirve de caché
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

---

## Instrucciones del Dockerfile

**FROM** — define la imagen base sobre la que se construye. Toda imagen parte de otra imagen (o de `scratch` para imágenes vacías). Es siempre la primera instrucción.

```dockerfile
FROM python:3.11-alpine
```

**WORKDIR** — establece el directorio de trabajo dentro del contenedor. Los comandos `COPY`, `RUN` y `CMD` posteriores operan relativos a este directorio. Si no existe, Docker lo crea.

```dockerfile
WORKDIR /app
```

**COPY** — copia archivos del contexto de build al sistema de archivos de la imagen. Es la instrucción preferida frente a `ADD` para copiar archivos locales.

```dockerfile
COPY requirements.txt .
COPY app/ /app/
```

**ADD** — igual que `COPY` pero con dos capacidades extra: puede descomprimir archivos `.tar` automáticamente y puede descargar URLs remotas. Se prefiere `COPY` cuando no se necesitan esas funciones porque su comportamiento es más predecible.

```dockerfile
ADD archivo.tar.gz /app/
```

**RUN** — ejecuta un comando durante el build y guarda el resultado como una nueva capa. Se usa para instalar dependencias, compilar código o configurar el sistema.

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**ENV** — define variables de entorno disponibles tanto durante el build como en tiempo de ejecución del contenedor.

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1
```

**EXPOSE** — documenta el puerto en el que escucha la aplicación. No publica el puerto en el host; es solo metadato informativo para quien use la imagen. El puerto se publica realmente con `-p` en `docker run`.

```dockerfile
EXPOSE 8000
```

**CMD** — define el comando por defecto que se ejecuta al arrancar el contenedor. Puede ser sobreescrito pasando un comando diferente a `docker run`. Solo puede haber un `CMD`; si hay varios, el último tiene efecto.

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**ENTRYPOINT** — define el ejecutable principal del contenedor. A diferencia de `CMD`, no se sobreescribe fácilmente; los argumentos de `docker run` se pasan como argumentos al `ENTRYPOINT`. Se usa cuando el contenedor debe comportarse siempre como un ejecutable concreto.

```dockerfile
ENTRYPOINT ["uvicorn"]
CMD ["main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**ARG** — define variables disponibles solo durante el build, no en tiempo de ejecución. Se usan para parametrizar el Dockerfile sin exponer valores en la imagen final.

```dockerfile
ARG APP_VERSION=1.0
```

---

## CMD vs ENTRYPOINT

La diferencia clave es cómo reaccionan ante argumentos pasados en `docker run`:

| | CMD | ENTRYPOINT |
|---|---|---|
| Se puede sobreescribir con `docker run <imagen> <comando>` | Sí, completamente | No; el argumento se añade al ENTRYPOINT |
| Uso típico | Argumentos por defecto | Ejecutable fijo del contenedor |

Con `CMD` solo:
```
docker run mi-imagen python otro_script.py  # sobreescribe CMD completo
```

Con `ENTRYPOINT ["python"]` y `CMD ["main.py"]`:
```
docker run mi-imagen otro_script.py  # ejecuta: python otro_script.py
```

En la práctica, la combinación `ENTRYPOINT` + `CMD` se usa cuando el contenedor debe ser siempre el mismo ejecutable pero con argumentos configurables.

---

## Imagen base Alpine

Alpine Linux es una distribución minimalista basada en musl libc y BusyBox. Pesa aproximadamente 5 MB frente a los 60-120 MB de Debian o Ubuntu.

Por qué se prefiere en contenedores:

- **Tamaño**: imágenes más pequeñas se descargan y despliegan más rápido, y ocupan menos espacio en el registro.
- **Superficie de ataque reducida**: menos paquetes instalados significa menos vulnerabilidades potenciales.
- **Arranque más rápido**: menos capas y menos sistema de ficheros que inicializar.

El inconveniente principal es la compatibilidad: Alpine usa `musl libc` en lugar de `glibc`, lo que puede causar problemas con algunas librerías compiladas para glibc (ciertos paquetes Python con extensiones C). En esos casos se usa `python:3.11-slim` (Debian sin paquetes no esenciales) como alternativa de equilibrio.

---

## Build, ejecución e inspección de la imagen propia (paso 6)

### Construcción

```
docker build -t sysadmin-toolkit:fase8 .
```

Las instrucciones se ejecutan en orden: `FROM` → `WORKDIR` → `COPY requirements.txt` → `RUN pip install` → `COPY app/` → `EXPOSE` → `CMD`. Cada `RUN`/`COPY` genera su capa.

### Comportamiento de la caché

Tras un primer build completo, se cambió `app/main.py` y se volvió a construir. Solo se reconstruyó la última capa, el resto se sirvió de caché:

```
#6 [2/5] WORKDIR /app          CACHED
#7 [3/5] COPY requirements.txt CACHED
#8 [4/5] RUN pip install        CACHED
#9 [5/5] COPY app/ .            (reconstruida)
```

Esto confirma el motivo del orden del Dockerfile: como `requirements.txt` se copia y se instala **antes** de copiar el código, tocar `main.py` no invalida la capa de `pip install`, que es la cara (51 MB y varios segundos). Si se hubiera hecho `COPY . .` antes del `pip install`, cada cambio en el código reinstalaría todas las dependencias.

### Ejecución y Swagger

```
docker run --rm -p 8000:8000 sysadmin-toolkit:fase8
```

Con el puerto publicado, la Swagger UI automática de FastAPI queda en `http://localhost:8000/docs`, desde donde se prueban los endpoints (`/health`, `/inventory`, etc.). En el stack final el puerto no se publica: solo se accede vía NGINX.

### Tamaño real e history

```
docker images sysadmin-toolkit:fase8
# sysadmin-toolkit:fase8   151MB
```

`docker history` muestra de qué se compone ese tamaño:

| Capa | Tamaño |
|---|---|
| `ADD alpine-minirootfs` (base) | 9.07 MB |
| `RUN apk add ... build Python` (capas de `python:3.11-alpine`) | ~51 MB |
| `RUN pip install -r requirements.txt` (FastAPI, uvicorn, redis) | 51.1 MB |
| `COPY app/requirements.txt` | 12.3 kB |
| `COPY app/ .` (código + auth.log + inventory.csv) | 20.5 kB |
| `WORKDIR`, `EXPOSE`, `CMD` | 0 B |

El peso vive en la imagen base de Python y en las dependencias, **no** en el código propio, que apenas ocupa 33 kB entre las dos capas de `COPY`.

### Optimización del tamaño

Lo ya aplicado en este Dockerfile:

- **Base `alpine`** en vez de `python:3.11` (que ronda los 1 GB).
- **`pip install --no-cache-dir`**: pip no guarda el caché de descarga dentro de la imagen.
- **`COPY` selectivo del código** vía `.dockerignore`, que excluye `docs/`, `.git/`, `__pycache__/`, `.venv/` y `.env` del contexto de build.

Siguientes pasos posibles si hiciera falta bajar más: un **multi-stage build** (compilar dependencias en una etapa y copiar solo los artefactos a una imagen final limpia) y consolidar instrucciones `RUN` para reducir el número de capas.
