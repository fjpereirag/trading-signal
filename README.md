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
El panel de Quantfury recibe cifras introducidas manualmente, precargadas con una
captura del 23/09/2026 (saldo real protegido $500, poder $10.000, asignado
$9.278,47 y saldo trading $212,83). No se actualizan solas. El límite de
exposición del 30% es un supuesto editable; la estrategia original no da un
porcentaje. El panel bloquea sugerencias de compra al superarlo. La regla del
40% del saldo real se muestra como advertencia sobre el saldo de trading,
porque «margen libre» no tiene una equivalencia confirmada en Quantfury.
No predice liquidaciones ni promete conservar el capital. Una venta para
proteger el riesgo puede implicar pérdidas y prevalece sobre la regla general
de vender solo con beneficios. Las alertas de Telegram siguen siendo señales
técnicas, sin información de la cuenta y sin ejecución de operaciones.
