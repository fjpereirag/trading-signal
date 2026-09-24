# Agente Trading Móvil

Interfaz simplificada para tomar decisiones desde el teléfono.

## Pantalla principal
- Señal técnica alcista / bajista / esperar, separada de la revisión de riesgo
- M15: tendencia
- M5: confirmación
- M1: gatillo de entrada
- 3/3 = las tres reglas están cumplidas; NO significa 3/3 operaciones ganadoras.
- El stop de beneficios del documento no se calcula con un porcentaje fijo al entrar.

## Ejecutar
Instala Python 3.11+ en un ordenador/servidor:

    pip install -r requirements.txt
    streamlit run app.py

Streamlit mostrará una URL. Para usarlo cómodamente en el móvil hay que alojar la app
en un servicio web; no es necesario instalar Python en el teléfono.

## Seguridad
No solicita credenciales de Quantfury y no envía órdenes. La decisión y ejecución siguen
siendo manuales. El feed externo puede diferir del precio ejecutable de Quantfury.

## Revisión V4 de la posición XRP
El panel web usa cifras introducidas manualmente; revísalas antes de usarlo.
El límite de exposición del 30% es un supuesto editable. El bot usa el poder
asignado respecto del poder total para bloquear avisos de compra cuando la
cuenta Quantfury esté conectada. La regla del 40% del saldo real se presenta
solo como advertencia: no existe equivalencia confirmada con «margen libre».
Los precios externos pueden diferir de los de Quantfury. Las operaciones
siguen siendo manuales.

## Consulta Quantfury desde GitHub Actions (preparación)

El flujo admite el secreto `QUANTFURY_ACCESS_TOKEN` para consultar, en modo
lectura, la cuenta de trading y las posiciones abiertas mediante el MCP oficial.
Si está configurado y la consulta falla, el trabajo se detiene y no sustituye
la cuenta por las cifras antiguas del panel. La exposición se calcula como
`(tradingPower - availableTradingPower) / tradingPower`; incluye poder asignado
a posiciones y órdenes activas. Con 30% o más se omiten avisos de compra XRP.

La autorización de ChatGPT no entrega un token a GitHub Actions. Para que la
consulta sea permanente hace falta un método OAuth de Quantfury para ejecución
desatendida: un access token temporal caducará. No copies la sesión, cookies
ni credenciales de ChatGPT al repositorio. Hasta configurar esa autenticación,
los avisos siguen siendo técnicos y externos. Nunca se envían órdenes.
