# NGINX como proxy inverso

## Proxy directo vs proxy inverso

Un proxy directo está delante de los clientes: el cliente lo configura a propósito para que sus peticiones salgan por ahí, normalmente para saltarse un bloqueo o anonimizar el origen (la empresa que filtra qué páginas puede visitar su gente, por ejemplo).

Un proxy inverso está delante de los servidores. El cliente ni sabe que existe: pide algo a `localhost` y quien responde de verdad es NGINX, que reenvía la petición a quien corresponda (en este caso, al backend) y devuelve la respuesta como si fuera suya. El cliente nunca habla directamente con el backend.

## Por qué NGINX delante de la API en producción

- **Gestión SSL/TLS centralizada**: el certificado se configura una vez en NGINX, no en cada servicio que levantes detrás.
- **Rate limiting**: NGINX puede frenar a un cliente que hace demasiadas peticiones por segundo antes de que esa carga llegue siquiera al backend.
- **Caché de respuestas y archivos estáticos**: NGINX puede servir directamente lo que no cambia (imágenes, CSS, HTML) sin molestar al backend, que se reserva para lógica de negocio.
- **Aislamiento**: el backend nunca publica su puerto al host. Solo NGINX es visible desde fuera. Si hay una vulnerabilidad en el backend, atacarlo directamente desde fuera de la red Docker no es una opción.

## Upstream y server block

- **`upstream`**: define un grupo de servidores a los que NGINX puede reenviar tráfico. Aquí solo hay uno (`backend:8000`), pero en producción real podrían ser varias réplicas del mismo backend, y NGINX repartiría la carga entre ellas (load balancing).
- **`server`**: define cómo NGINX escucha una petición entrante (puerto, dominio, certificados) y qué hace con ella. Dentro de cada `server`, los bloques `location` deciden, según la ruta pedida, si la sirve él mismo (estáticos) o la reenvía con `proxy_pass` al `upstream`.

## Por qué NGINX rinde mejor que Apache bajo carga

Apache, en su modelo clásico, lanza un proceso o hilo por conexión entrante. Con miles de conexiones simultáneas eso significa miles de procesos compitiendo por CPU y memoria. NGINX usa un modelo asíncrono basado en eventos: un número fijo y pequeño de procesos worker gestiona miles de conexiones a la vez sin bloquearse esperando I/O. Por eso NGINX escala mejor cuantas más conexiones concurrentes hay, que es exactamente el escenario de un proxy inverso en producción.

## HTTPS local y rate limiting en este proyecto

El `nginx.conf` de este repo:
- Redirige todo el tráfico del puerto 80 al 443 (`return 301 https://...`), nunca se sirve sin cifrar.
- Usa un certificado autofirmado (ver `certs/README.md`) solo válido para desarrollo local.
- Limita a 5 peticiones/segundo por IP (`limit_req_zone`), con una ráfaga de 10 antes de empezar a rechazar, para frenar ataques de fuerza bruta contra la API.
- Sirve `/static/` directamente desde disco, sin tocar el backend.
