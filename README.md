# Consulta XRP/USDT

La [app Streamlit](https://trading-signal-fd3u8cqcappfwgngqujg8vp.streamlit.app/) ofrece un botón para consultar la cuenta de Quantfury y las velas completadas de Binance Spot XRP/USDT. GitHub Actions calcula tres indicaciones sobre acción, stop y parcial, y Streamlit las muestra al terminar. No se envían órdenes, no se mueven fondos y no se necesita Telegram.

Cada consulta vuelve a leer la cuenta y los datos de mercado. El flujo se detiene si la autorización falla, faltan velas recientes o los datos de la posición son incompletos. GitHub Actions no garantiza respuesta instantánea ni sustituye los stops colocados en Quantfury.

## Configurar la app

Sigue [README_WEBAPP.md](README_WEBAPP.md). Streamlit necesita `GH_WORKFLOW_DISPATCH_TOKEN` con permiso `Actions: read and write` y `APP_ACTION_PASSWORD`. El repositorio GitHub Actions necesita un secreto `APP_RESULT_PASSWORD` con el mismo valor de la clave de Streamlit. Las respuestas se guardan cifradas durante un día como artefactos de GitHub.

## Volver a autorizar Quantfury

Si falla la renovación de Quantfury, desde tu propio ordenador con Python 3.11+ y GitHub CLI autenticado ejecuta:

```powershell
py -m pip install requests
py connect_quantfury.py
```

El script abre la autorización en el navegador local y guarda `QUANTFURY_CLIENT_ID` y `QUANTFURY_REFRESH_TOKEN` como secretos del repositorio. El secreto `GH_SECRETS_PAT` debe tener permiso `Secrets: read and write` para el mismo repositorio y permite guardar automáticamente un token de renovación rotado. No copies tokens o códigos de autorización en el repositorio ni en chats.

## Ejecutar pruebas locales

```sh
pip install -r requirements.txt
python -m unittest test_quantfury_account.py test_alert_bot.py test_run_now.py test_result_codec.py
```
