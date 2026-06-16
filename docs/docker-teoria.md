# Docker: teoría de contenedores

## VM vs contenedor

Una máquina virtual emula hardware completo. Tiene su propio kernel, su propio sistema de archivos, sus propios drivers. Para arrancar una VM de Ubuntu necesitas asignarle RAM, disco y CPU dedicados, y esperar a que arranque el sistema operativo completo. Si quieres correr cinco servicios, necesitas cinco kernels distintos corriendo en paralelo.

Un contenedor no virtualiza hardware. Comparte el kernel del host directamente y usa dos características del kernel de Linux para crear aislamiento: **namespaces** (separan lo que el proceso puede ver: su PID, su red, su sistema de archivos) y **cgroups** (limitan los recursos que puede consumir: CPU, RAM, disco). El resultado es un proceso aislado que arranca en milisegundos y ocupa megabytes en lugar de gigabytes.

Lo que el contenedor **comparte** con el host:
- El kernel de Linux
- Los drivers de red y almacenamiento del host
- El hardware físico (CPU, RAM, disco) gestionado por el scheduler del SO

Lo que el contenedor **aísla**:
- Su sistema de archivos (basado en la imagen, con una capa de escritura efímera encima)
- Su tabla de procesos (desde dentro, el PID 1 es el proceso principal del contenedor)
- Su interfaz de red virtual
- Sus variables de entorno y usuarios

La consecuencia práctica: una imagen de 80MB arranca en menos de un segundo. Una VM equivalente pesa varios GB y tarda minutos.

---

## Conceptos clave

**Imagen**: plantilla de solo lectura que define el sistema de archivos del contenedor. Es inmutable. Funciona como un snapshot del sistema en un estado concreto. Se construye en capas; cada instrucción del Dockerfile añade una capa nueva encima de las anteriores.

**Contenedor**: instancia en ejecución de una imagen. Añade una capa de escritura efímera sobre las capas de la imagen. Cuando el contenedor se elimina, esa capa desaparece. La imagen original no se modifica.

**Dockerfile**: archivo de texto con las instrucciones para construir una imagen. Define desde qué imagen base partir, qué archivos copiar, qué comandos ejecutar durante el build y cómo arrancar la aplicación.

**Docker Hub**: registro público de imágenes, similar a GitHub pero para imágenes Docker. De aquí se descargan las imágenes oficiales (`python:3.11-alpine`, `nginx:alpine`, `redis:7`).

**Capa**: cada instrucción `RUN`, `COPY` o `ADD` del Dockerfile genera una capa independiente en el sistema de archivos de la imagen. Las capas se cachean: si no han cambiado, Docker las reutiliza en rebuilds posteriores. Por eso el orden importa: las instrucciones que cambian con frecuencia deben ir al final.

**Registro**: servidor que almacena y distribuye imágenes. Docker Hub es el registro público por defecto. En entornos de empresa se usan registros privados (GitHub Container Registry, AWS ECR, etc.).

---

## Ciclo de vida de un contenedor

```
[imagen]
    │
    │ docker run / docker create
    ▼
[created] ──── docker start ────► [running]
                                       │
                              docker pause / docker stop
                                       │
                                  [paused / stopped]
                                       │
                              docker start (desde stopped)
                              docker unpause (desde paused)
                                       │
                                  [running]
                                       │
                               docker rm / --rm
                                       ▼
                                  [eliminado]
```

Estados:
- **created**: el contenedor existe pero no ha arrancado el proceso principal.
- **running**: el proceso principal está activo.
- **paused**: los procesos están congelados con SIGSTOP; el contenedor sigue ocupando memoria.
- **stopped/exited**: el proceso principal terminó o fue detenido con SIGTERM/SIGKILL.
- **eliminado**: el contenedor ya no existe. La capa de escritura efímera se borra con él.

Los **datos escritos dentro del contenedor** (en su capa efímera) desaparecen al eliminarlo. Para que persistan hay que usar volúmenes Docker o bind mounts, que viven fuera del ciclo de vida del contenedor.

---

## Relación: kernel host → Docker Engine → contenedores

```
┌─────────────────────────────────────────────────────────┐
│                      Hardware físico                    │
│               (CPU, RAM, disco, red)                    │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   Kernel de Linux                       │
│         (namespaces, cgroups, OverlayFS)                │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   Docker Engine                         │
│  dockerd (daemon) + containerd + runc                   │
│  Gestiona imágenes, redes, volúmenes y contenedores     │
└──────────┬────────────┬────────────────┬────────────────┘
           │            │                │
    ┌──────▼───┐  ┌─────▼────┐  ┌───────▼──────┐
    │container1│  │container2│  │  container3  │
    │ (FastAPI)│  │ (Redis)  │  │   (NGINX)    │
    │ PID ns   │  │ PID ns   │  │   PID ns     │
    │ net ns   │  │ net ns   │  │   net ns     │
    └──────────┘  └──────────┘  └──────────────┘
```

Docker Engine no es un hipervisor. Es un proceso en espacio de usuario (`dockerd`) que habla con el kernel para crear y gestionar namespaces y cgroups. `containerd` gestiona el ciclo de vida de los contenedores y `runc` es quien realmente llama a las syscalls del kernel para crearlos. Desde fuera parecen procesos aislados; desde dentro, cada contenedor cree que es el único sistema corriendo.
