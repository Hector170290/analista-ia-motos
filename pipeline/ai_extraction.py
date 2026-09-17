import json
import os

from openai import OpenAI


PROMPT_EXTRACCION = """
Eres un analista comercial de una empresa comercializadora de motocicletas.

Analiza la conversación proporcionada y extrae ÚNICAMENTE información
que el cliente haya declarado explícita o claramente.

No inventes información.
Si un dato no aparece, utiliza null.
No supongas presupuesto, modelo, forma de pago o intención.

Devuelve únicamente un JSON válido con esta estructura:

{
    "modelo_conversacion": null,
    "modelos_alternativos": [],
    "presupuesto": null,
    "cuota_inicial": null,
    "forma_pago": null,
    "intencion_compra": null,
    "objecion_principal": null,
    "solicita_cotizacion": false,
    "solicita_visita": false,
    "resumen_conversacion": null,
    "confianza_extraccion": 0.0
}

Reglas:

- modelo_conversacion:
  Modelo de motocicleta que el cliente muestra mayor intención de comprar.
  No inventar el modelo si solamente menciona una marca.

- modelos_alternativos:
  Otros modelos mencionados explícitamente.

- presupuesto:
  Presupuesto declarado por el cliente, si existe.

- cuota_inicial:
  Cuota inicial o entrada declarada por el cliente, si existe.

- forma_pago:
  Usa únicamente:
  "contado", "financiado", "indefinido".

- intencion_compra:
  Clasifica como:
  "alta", "media", "baja".

- objecion_principal:
  Principal obstáculo mencionado por el cliente.
  Si no existe, usa "ninguna".

- solicita_cotizacion:
  true únicamente si el cliente solicita una cotización,
  precio formal o propuesta comercial.

- solicita_visita:
  true únicamente si el cliente solicita o acepta explícitamente
  una visita al punto de venta.

- resumen_conversacion:
  Resumen breve y objetivo.

- confianza_extraccion:
  Número entre 0 y 1.
"""


def extraer_informacion_conversacion(texto_conversacion):
    """
    Extrae información comercial estructurada de una conversación
    utilizando un modelo de IA.
    """

    if not texto_conversacion:
        return None

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "No se encontró la variable de entorno OPENAI_API_KEY."
        )

    client = OpenAI(api_key=api_key)

    respuesta = client.responses.create(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": PROMPT_EXTRACCION,
            },
            {
                "role": "user",
                "content": texto_conversacion,
            },
        ],
        extra_headers={
            "Accept-Encoding": "identity"
        },
    )

    contenido = respuesta.output_text.strip()

    try:
        resultado = json.loads(contenido)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"La IA no devolvió un JSON válido: {contenido}"
        ) from error

    return resultado


def enriquecer_conversaciones(df, limite=None):
    """
    Aplica extracción de IA a las conversaciones.

    limite permite procesar una cantidad pequeña durante las pruebas.
    Si es None, procesa todas las conversaciones.
    """

    df = df.copy()

    columnas_ia = [
        "modelo_conversacion",
        "modelos_alternativos",
        "presupuesto",
        "cuota_inicial",
        "forma_pago",
        "intencion_compra",
        "objecion_principal",
        "solicita_cotizacion",
        "solicita_visita",
        "resumen_conversacion",
        "confianza_extraccion",
    ]

    for columna in columnas_ia:
        df[columna] = None

    indices = df[
        df["texto_conversacion"].notna()
    ].index

    if limite is not None:
        indices = indices[:limite]

    for indice in indices:

        resultado = extraer_informacion_conversacion(
            df.at[indice, "texto_conversacion"]
        )

        if resultado:

            for columna in columnas_ia:
                df.at[indice, columna] = resultado.get(
                    columna
                )

    return df