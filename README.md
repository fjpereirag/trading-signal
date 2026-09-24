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

## Conexión programada de Quantfury (experimental)

GitHub Actions no recibe la autorización del complemento de ChatGPT. Para crear
una autorización OAuth independiente, en tu propio ordenador con Python 3.11+
y GitHub CLI instalado y autenticado (`gh auth login`), ejecuta:

```powershell
py -m pip install -r requirements.txt
py connect_quantfury.py
```

El script abre Quantfury en el navegador de ese ordenador, recibe el retorno en
`127.0.0.1`, intercambia el código con PKCE y guarda el identificador del
cliente y el token de renovación como secretos cifrados del repositorio. Nunca
copies contraseñas, códigos ni tokens a este repositorio o a un chat. El script
requiere que Quantfury conceda un `refresh_token`; de lo contrario, se detiene.

Si Quantfury rota el token de renovación, GitHub Actions solo puede guardar el
nuevo si dispone de `GH_SECRETS_PAT`: un token de GitHub limitado al repositorio
`fjpereirag/trading-signal` con permiso **Secrets: write**. El script permite
introducirlo sin mostrarlo y guardarlo como secreto. Si lo omites y Quantfury
rota el token, el bot fallará de forma visible y requerirá una nueva
configuración local. Esta opción da al workflow capacidad de cambiar secretos;
revoca el token en GitHub si dejas de usar la integración.

No hay garantía de que Quantfury acepte este cliente ni de que la autorización
sea estable: todavía hace falta una prueba real de extremo a extremo. El bot
solo llama a herramientas de lectura de cuenta y posiciones y nunca envía
órdenes. Si la lectura falla, no envía avisos que aparenten tener datos de la
cuenta. GitHub puede retrasar u omitir ejecuciones programadas, por lo que las
alertas no son una protección en tiempo real.
