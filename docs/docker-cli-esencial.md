# Docker: comandos esenciales de la CLI

## Gestión de imágenes

```
docker pull nginx:alpine        # descarga una imagen de Docker Hub
docker images                   # lista imágenes locales
docker inspect nginx:alpine     # muestra metadatos completos en JSON
docker rmi hello-world          # elimina una imagen local
```

## Contenedor NGINX en segundo plano

```
docker run -d --name nginx-test -p 8080:80 nginx:alpine
```

- `-d` corre el contenedor en segundo plano (detached)
- `-p 8080:80` mapea el puerto 8080 del host al 80 del contenedor
- Accesible en http://localhost:8080

## Gestión de contenedores

```
docker ps           # contenedores en ejecución
docker ps -a        # todos los contenedores (incluyendo detenidos)
docker stop nginx-test
docker start nginx-test
docker restart nginx-test
docker rm -f nginx-test     # elimina forzando aunque esté corriendo
```

## docker exec

```
docker exec -it nginx-test sh
```

Abre una shell interactiva dentro de un contenedor en ejecución. Lo que se instala dentro (ej. `apk add curl`) vive en la capa de escritura efímera del contenedor. Al hacer `docker rm` esa capa desaparece — el siguiente contenedor parte de la imagen limpia.

Nota: `nginx:alpine` ya incluye `curl` en la imagen base (versión 8.19.0), por lo que el experimento de pérdida de datos no es observable con esta imagen.

## Inspección en profundidad

```
docker inspect nginx-test --format "Status: {{.State.Status}}"
docker inspect nginx-test --format "{{range .NetworkSettings.Networks}}IP: {{.IPAddress}} | Gateway: {{.Gateway}}{{end}}"
```

Resultado:

```
Status: running
IP: 172.17.0.2 | Gateway: 172.17.0.1
```

La IP `172.17.0.2` es interna a la red bridge de Docker. Desde fuera solo se accede a través del puerto publicado. El gateway `172.17.0.1` es la interfaz `docker0` del host.

## Logs en tiempo real

```
docker logs -f nginx-test
```

Muestra los logs del proceso principal del contenedor en tiempo real. Ejemplo de entrada al acceder desde el navegador:

```
172.17.0.1 - - [09/Jun/2026:08:58:08 +0000] "GET / HTTP/1.1" 304 0 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36" "-"
```

`Ctrl+C` para salir del seguimiento sin detener el contenedor.
