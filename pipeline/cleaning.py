from pipeline.normalization import (
    normalizar_dataframe,
    normalizar_fecha,
    normalizar_ciudad,
)

from pipeline.model_homologation import homologar_dataframe


def limpiar_leads(leads, catalogo):
    """
    Ejecuta el proceso de limpieza y homologación
    sobre el DataFrame de leads.
    """

    df = leads.copy()

    # Normalización de texto y teléfono
    df = normalizar_dataframe(
        df,
        columnas_texto=[
            "nombre_cliente",
            "email",
            "ciudad",
            "modelo_interes_texto",
        ],
        columna_telefono="telefono",
    )

    # Normalización de fecha
    if "fecha_registro" in df.columns:
        df["fecha_registro_normalizada"] = (
            df["fecha_registro"].apply(normalizar_fecha)
        )

    # Normalización de ciudad
    if "ciudad" in df.columns:
        df["ciudad_normalizada"] = (
            df["ciudad"].apply(normalizar_ciudad)
        )

    # Homologación del modelo contra el catálogo
    df = homologar_dataframe(df, catalogo)

    return df

    