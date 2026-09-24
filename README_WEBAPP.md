# Trading Signal — Web-App móvil

Web-app sencilla para consultar señales desde Android/iPhone sin instalar Python en el teléfono.

## Qué verá el usuario
1. Activo.
2. Señal técnica alcista / bajista / esperar y revisión manual de riesgo.
3. M15 tendencia, M5 confirmación, M1 entrada.
4. No propone stop ni venta con beneficio sin datos suficientes de la posición.
5. Detalle técnico oculto en "¿Por qué esta señal?".

## Publicarla en Streamlit Community Cloud
1. Crea un repositorio privado o público en GitHub.
2. Sube todos los archivos de esta carpeta a la raíz del repositorio.
3. En Streamlit Community Cloud crea una nueva app.
4. Selecciona el repositorio y `app.py`.
5. Despliega la app.
6. Abre la URL resultante en Chrome/Safari del móvil.
7. Android: menú ⋮ > "Añadir a pantalla de inicio".
   iPhone: Compartir > "Añadir a pantalla de inicio".

No introduzcas credenciales de Quantfury en esta app.

## Botón «Ejecutar todo ahora»

La aplicación muestra un botón para abrir el workflow de GitHub. Si la web-app
está publicada en Streamlit y configuras estos **secrets de Streamlit**,
aparece además el botón directo, protegido por clave:

```toml
GH_WORKFLOW_DISPATCH_TOKEN = "token fine-grained de GitHub"
APP_ACTION_PASSWORD = "una clave larga y única"
```

El token debe limitarse al repositorio `fjpereirag/trading-signal` y al
permiso **Actions: write**. No uses el token de renovación de Quantfury en
Streamlit. Tras pulsar, GitHub Actions realiza la consulta con sus secretos
ya existentes; la confirmación de la web significa que GitHub aceptó el
encargo, no que Telegram haya recibido el mensaje. Comprueba el resultado en
la pestaña Actions. La app publicada debe tener acceso restringido, porque
una clave de formulario por sí sola no sustituye la autenticación de GitHub.

## Nota
La web-app es un asistente externo de análisis y no inicia, modifica ni cierra posiciones.
Los precios de Yahoo Finance pueden retrasarse o diferir del precio ejecutable.
