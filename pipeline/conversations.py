import pandas as pd


def preparar_conversaciones(conversaciones):
    """
    Convierte las conversaciones en un DataFrame
    y consolida todas las conversaciones de cada lead
    en un solo registro.
    """

    registros = []

    for conversacion in conversaciones:
        lead_id = conversacion.get("lead_id")

        mensajes = conversacion.get("mensajes", [])

        textos = [
            mensaje.get("texto", "")
            for mensaje in mensajes
            if mensaje.get("texto")
        ]

        texto_completo = "\n".join(textos)

        registros.append({
            "lead_id": lead_id,
            "texto_conversacion": texto_completo,
            "numero_mensajes": len(mensajes),
        })

    df = pd.DataFrame(registros)

    # Consolidar múltiples conversaciones del mismo lead
    if not df.empty:

        df = (
            df.groupby("lead_id", as_index=False)
            .agg(
                texto_conversacion=(
                    "texto_conversacion",
                    lambda x: "\n".join(
                        texto for texto in x
                        if texto
                    )
                ),
                numero_mensajes=(
                    "numero_mensajes",
                    "sum"
                ),
            )
        )

    return df


def unir_conversaciones(leads, conversaciones_df):
    """
    Une las conversaciones con los leads.

    Se conserva todo el universo de leads,
    incluso aquellos que no tienen conversación.
    """

    df = leads.copy()

    df = df.merge(
        conversaciones_df,
        on="lead_id",
        how="left"
    )

    return df
    