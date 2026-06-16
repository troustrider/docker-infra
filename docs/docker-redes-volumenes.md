# Redes y volúmenes en Docker

## Redes: bridge, host y none

Docker trae tres tipos de red de fábrica:

- **bridge**: es la red por defecto. Docker crea una red virtual privada y cada contenedor recibe su propia IP dentro de ella. El contenedor no ve la red del host directamente, solo lo que se publica explícitamente con `-p`. Es la que usamos en este proyecto: backend y Redis viven en su propia red bridge, aislados del resto.
- **host**: el contenedor no tiene su propia pila de red, usa directamente la del host. Si el backend escucha en el puerto 8000, en modo host ese puerto ya está ocupado en la máquina real, sin necesidad de publicar nada. Se usa cuando necesitas rendimiento de red máximo o el contenedor tiene que ver la red del host tal cual (sniffers, VPNs), pero pierdes el aislamiento.
- **none**: el contenedor no tiene ninguna interfaz de red salvo loopback. Sirve para procesos que no necesitan red en absoluto, por ejemplo un job batch que solo procesa archivos locales.

En este proyecto solo usamos bridge, porque es la opción que da aislamiento real entre servicios.

## Service discovery interno de Compose

Cuando varios servicios están en la misma red de Compose, Docker levanta un DNS interno. Cada servicio es alcanzable por su nombre, no por IP. Por eso en el backend la conexión a Redis se hace contra el host `redis`, no contra una IP fija: Compose resuelve `redis` a la IP que le tocó en esa ejecución. Es el mismo concepto que un DNS interno de una LAN, salvo que aquí el "DNS" lo gestiona el propio motor de Docker y solo es visible para los contenedores de esa red.

## Puerto publicado vs puerto expuesto

- **Expuesto** (`EXPOSE` en el Dockerfile, o simplemente el puerto en el que escucha el proceso) solo es alcanzable desde otros contenedores de la misma red. No abre nada hacia el host ni hacia el exterior.
- **Publicado** (`ports:` en el Compose, o `-p` en `docker run`) crea un mapeo desde un puerto del host hacia el contenedor. Eso sí es accesible desde fuera.

La diferencia es de seguridad, no solo de sintaxis: en este proyecto el backend escucha en el 8000 pero **no se publica**. Solo NGINX publica el 80. Así, si alguien escanea la máquina desde fuera, solo ve el puerto de NGINX. El backend solo es alcanzable dentro de la red Docker, igual que tendrías un firewall que solo deja pasar el tráfico al proxy y bloquea el resto.

## Volúmenes: por qué los contenedores son efímeros

Un contenedor tiene su propio filesystem, pero esa capa es de escritura temporal: cuando el contenedor se elimina, esa capa se borra con él. Cualquier dato que tenga que sobrevivir necesita vivir fuera de esa capa.

Docker ofrece dos mecanismos:

- **Volumen nombrado**: lo gestiona Docker, vive en su propio almacenamiento (en Linux, bajo `/var/lib/docker/volumes/`). No te preocupas de dónde está físicamente, solo le pones un nombre y lo montas. Es la opción correcta para datos de aplicación, como los reports de este proyecto o los datos de Redis.
- **Bind mount**: monta una carpeta concreta del host dentro del contenedor. Tú controlas la ruta exacta. Es la opción correcta para configuración que quieres editar desde fuera sin reconstruir la imagen, como `nginx.conf`.

En este proyecto:
- `redis_data` (volumen nombrado) guarda la persistencia de Redis.
- `backend_data` (volumen nombrado) guarda `reports.json` que escribe el endpoint `POST /reports`.
- `./nginx.conf` (bind mount, solo lectura) monta la config de NGINX desde el repo.

### Experimento de persistencia

1. Levantar el backend y mandar un par de `POST /reports`.
2. Eliminar el contenedor del backend (`docker compose rm -f backend` o recrearlo con `docker compose up -d --force-recreate backend`).
3. Volver a pedir `GET /reports`: los datos siguen ahí porque vivían en el volumen `backend_data`, no en la capa de escritura del contenedor que se borró.
