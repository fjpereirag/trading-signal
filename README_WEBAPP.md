# Objetivos simulados en Streamlit

La página consulta el saldo y las posiciones de Quantfury, las velas de ETH y SOL en Binance y las de AVGO en Yahoo Finance al pulsar «Ejecutar todo ahora». GitHub Actions ejecuta la consulta y entrega a Streamlit una tabla cifrada de condiciones para una prueba simulada de +50 $ / −50 $. No se crean órdenes ni se ejecutan operaciones; los precios públicos no son las cotizaciones de compra y venta de Quantfury. Si hay una posición abierta, ninguna fila se marca como lista.

## Configuración de la clave de resultado

Conserva los secretos existentes de Streamlit `GH_WORKFLOW_DISPATCH_TOKEN` y `APP_ACTION_PASSWORD`. El token de GitHub necesita permiso **Actions: read and write** para el repositorio `fjpereirag/trading-signal`, porque además de iniciar el flujo recupera el resultado cifrado.

En [Settings → Secrets and variables → Actions](https://github.com/fjpereirag/trading-signal/settings/secrets/actions) conserva un secreto de repositorio llamado **`APP_RESULT_PASSWORD`** cuyo valor sea exactamente el mismo que el de `APP_ACTION_PASSWORD` en Streamlit. No uses el token de GitHub ni el token de Quantfury como contraseña. No publiques esa clave ni hagas capturas con ella visible.

Abre la [app](https://trading-signal-fd3u8cqcappfwgngqujg8vp.streamlit.app/), actualiza la página, introduce la clave y pulsa una vez. La respuesta aparecerá automáticamente en la pantalla al terminar GitHub Actions. Si el flujo falla, el enlace muestra el detalle de la ejecución.

El resultado se guarda cifrado como artefacto de GitHub con caducidad de un día. El repositorio es público; la contraseña compartida debe ser larga y única. No introduzcas cifras manuales: cada ejecución vuelve a consultar la cuenta y el mercado. La app indica la hora de cada vela y rechaza velas con más de doce minutos de antigüedad. El límite de 50 $ es una estimación de pérdida, no una garantía frente a saltos de precio.
