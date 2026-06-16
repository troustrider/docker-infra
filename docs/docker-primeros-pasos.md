# Docker: instalación y primer contacto

## Verificación de la instalación

### docker version

```
Client:
 Version:           29.5.2
 API version:       1.54
 Go version:        go1.26.3
 Git commit:        79eb04c
 Built:             Wed May 20 14:40:41 2026
 OS/Arch:           windows/amd64
 Context:           desktop-linux

Server: Docker Desktop 4.76.0 (228118)
 Engine:
  Version:          29.5.2
  API version:      1.54 (minimum version 1.40)
  Go version:       go1.26.3
  Git commit:       568f755
  Built:            Wed May 20 14:38:09 2026
  OS/Arch:          linux/amd64
  Experimental:     false
 containerd:
  Version:          v2.2.4
  GitCommit:        193637f7ee8ae5f5aa5248f49e7baa3e6164966e
 runc:
  Version:          1.3.5
  GitCommit:        v1.3.5-0-g488fc13e
 docker-init:
  Version:          0.19.0
  GitCommit:        de40ad0
```

### docker info (extracto relevante)

```
Kernel Version: 6.6.114.1-microsoft-standard-WSL2
Operating System: Docker Desktop
OSType: linux
Architecture: x86_64
CPUs: 4
Total Memory: 3.776GiB
Name: docker-desktop
ID: 0c07791e-69c7-4d6e-8f8d-bc186048111e
Docker Root Dir: /var/lib/docker
Debug Mode: false
HTTP Proxy: http.docker.internal:3128
HTTPS Proxy: http.docker.internal:3128
No Proxy: hubproxy.docker.internal
Labels: com.docker.desktop.address=npipe://\\.\pipe\docker_cli
Experimental: false
Insecure Registries:
  hubproxy.docker.internal:5555
  ::1/128
  127.0.0.0/8
Live Restore Enabled: false
Firewall Backend: iptables
```

El servidor corre sobre WSL2 (`linux/amd64`). El cliente es Windows nativo que habla con el daemon Linux vía named pipe. En Windows no se añade el usuario a un grupo docker — Docker Desktop gestiona los permisos automáticamente.

---

## Primer contenedor: hello-world

```
docker run --rm hello-world
```

Lo que hizo Docker internamente:

1. El cliente buscó la imagen `hello-world` en el almacén local → no existía.
2. La descargó automáticamente de Docker Hub (`docker pull hello-world`).
3. Creó un contenedor a partir de esa imagen y ejecutó su proceso principal.
4. El proceso terminó → el contenedor pasó a estado `exited`.
5. El flag `--rm` eliminó el contenedor automáticamente al salir.

La imagen sigue en local. El contenedor ya no existe.

---

## Contenedor interactivo: ubuntu:22.04

```
docker run --rm -it ubuntu:22.04 bash
```

Docker descargó la imagen desde Docker Hub al no encontrarla en local. Dentro del contenedor el usuario es `root` y el hostname es el ID corto del contenedor (`55e61b80cc2d`).

Tras ejecutar `exit`, `docker ps -a` devuelve lista vacía: el flag `--rm` eliminó el contenedor en cuanto terminó el proceso principal (`bash`). La imagen `ubuntu:22.04` sigue disponible en local; lo que desapareció es la instancia (capa de escritura efímera incluida).
