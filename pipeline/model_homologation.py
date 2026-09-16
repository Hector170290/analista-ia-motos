import re


def limpiar_modelo_para_homologacion(valor):
    """
    Prepara el texto del modelo para compararlo
    contra el catálogo.
    """

    if valor is None:
        return None

    texto = str(valor).strip().lower()

    # Correcciones frecuentes de escritura
    correcciones = {
        "a.k.t": "akt",
        "hnda": "honda",
        "suzuky": "suzuki",
        "bajai": "bajaj",
        "heroo": "hero",
    }

    for incorrecto, correcto in correcciones.items():
        texto = texto.replace(incorrecto, correcto)

    # Eliminar años de 4 dígitos
    texto = re.sub(r"\b(19|20)\d{2}\b", "", texto)

    # Normalizar espacios
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto if texto else None


def homologar_modelo(modelo, catalogo):
    """
    Busca una coincidencia exacta entre el modelo informado
    y los modelos disponibles en el catálogo.
    """

    modelo_limpio = limpiar_modelo_para_homologacion(modelo)

    if modelo_limpio is None:
        return None

    for _, fila in catalogo.iterrows():

        modelo_catalogo = (
            f"{fila['marca']} {fila['linea']}"
        )

        modelo_catalogo_limpio = (
            limpiar_modelo_para_homologacion(modelo_catalogo)
        )

        if modelo_limpio == modelo_catalogo_limpio:
            return modelo_catalogo

    return None


def homologar_dataframe(df_leads, catalogo):
    """
    Homologa los modelos de todos los leads
    contra el catálogo de motos.
    """

    df = df_leads.copy()

    df["modelo_homologado"] = (
        df["modelo_interes_texto"]
        .apply(lambda x: homologar_modelo(x, catalogo))
    )

    df["estado_modelo"] = "MODELO_NO_IDENTIFICADO"

    df.loc[
        df["modelo_interes_texto"].isna(),
        "estado_modelo"
    ] = "SIN_MODELO"

    df.loc[
        df["modelo_homologado"].notna(),
        "estado_modelo"
    ] = "HOMOLOGADO"

    return df

