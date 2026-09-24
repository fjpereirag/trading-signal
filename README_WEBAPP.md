# XRP/USDT — aplicación Streamlit

La pantalla tiene un botón para consultar la cuenta Quantfury y las velas completadas de Binance Spot XRP/USDT. GitHub Actions ejecuta la consulta y envía el resultado a Telegram; la app no realiza operaciones ni muestra cifras introducidas a mano.

## Botón «Ejecutar todo ahora»

En los secretos de Streamlit configura:

```toml
GH_WORKFLOW_DISPATCH_TOKEN = "token fine-grained de GitHub"
APP_ACTION_PASSWORD = "una clave larga y única"
```

El token debe estar limitado al repositorio `fjpereirag/trading-signal` y contar con **Actions: write**. Es distinto del token `GH_SECRETS_PAT` guardado en GitHub para la renovación de Quantfury. El botón confirma que GitHub aceptó la solicitud; consulta el enlace «Ver estado de las consultas» para comprobar si terminó correctamente. La señal llegará a Telegram si se pudieron leer las fuentes y completar el análisis.

La app publicada es accesible mediante URL. Protege el acceso de Streamlit cuando esté disponible; la clave del formulario protege el botón pero no sustituye una autenticación completa.

## Uso

Abre la app, introduce la clave y pulsa «Ejecutar todo ahora». Las operaciones de Quantfury se efectúan manualmente.
