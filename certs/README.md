# Certificados autofirmados

Este directorio no se sube al repo (ver `.gitignore`). Para generar el par clave/certificado local antes de levantar el proxy:

```bash
openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout certs/selfsigned.key \
  -out certs/selfsigned.crt \
  -subj "/CN=localhost"
```

El navegador avisará de que el certificado no es de confianza porque está autofirmado, eso es esperado en local. En producción real ese certificado lo emitiría una CA (por ejemplo Let's Encrypt).
