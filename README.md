# Agente Trading Móvil

Interfaz simplificada para tomar decisiones desde el teléfono.

## Pantalla principal
- COMPRAR / VENDER / ESPERAR
- M15: tendencia
- M5: confirmación
- M1: gatillo de entrada
- 3/3 = las tres reglas están cumplidas; NO significa 3/3 operaciones ganadoras.
- Entrada, stop, objetivo y riesgo solo aparecen cuando hay señal.

## Ejecutar
Instala Python 3.11+ en un ordenador/servidor:

    pip install -r requirements.txt
    streamlit run app.py

Streamlit mostrará una URL. Para usarlo cómodamente en el móvil hay que alojar la app
en un servicio web; no es necesario instalar Python en el teléfono.

## Seguridad
No solicita credenciales de Quantfury y no envía órdenes. La decisión y ejecución siguen
siendo manuales. El feed externo puede diferir del precio ejecutable de Quantfury.
