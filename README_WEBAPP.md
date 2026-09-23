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

## Nota
La web-app es un asistente externo de análisis y no inicia, modifica ni cierra posiciones.
Los precios de Yahoo Finance pueden retrasarse o diferir del precio ejecutable.
