import pandas as pd


def calcular_prioridad(fila):
    """
    Clasifica un lead según señales comerciales explícitas.

    La prioridad no intenta predecir una probabilidad exacta
    de cierre. Sirve para ordenar la gestión comercial.
    """

    # Sin modelo identificado:
    # no se debe asumir qué moto quiere el cliente.
    if pd.isna(fila.get("modelo_homologado")):
        return "PENDIENTE_MODELO"

    intencion = fila.get("intencion_compra")
    cotizacion = fila.get("solicita_cotizacion")
    visita = fila.get("solicita_visita")
    forma_pago = fila.get("forma_pago")
    cuota_inicial = fila.get("cuota_inicial")

    # Señales de intención
    if intencion == "alta":
        return "ALTA"

    # Solicitar cotización o visita es una acción comercial concreta.
    if cotizacion is True or visita is True:
        return "ALTA"

    # Señales comerciales intermedias
    if intencion == "media":
        return "MEDIA"

    if forma_pago in ["contado", "financiado"]:
        return "MEDIA"

    if pd.notna(cuota_inicial):
        return "MEDIA"

    # Si existe modelo pero no hay señales comerciales fuertes.
    return "BAJA"


def aplicar_priorizacion(df):
    """
    Aplica la regla de priorización a todo el DataFrame.
    """

    resultado = df.copy()

    resultado["prioridad"] = resultado.apply(
        calcular_prioridad,
        axis=1
    )

    return resultado
    