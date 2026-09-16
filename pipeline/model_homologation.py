import re


def limpiar_modelo_para_homologacion(valor):
    """
    Prepara el texto del modelo para compararlo
    contra el catálogo.
    """

    if valor is None:
        return None

    texto = str(valor).strip().lower()

    # Eliminar años de 4 dígitos
    texto = re.sub(r"\b(19|20)\d{2}\b", "", texto)

    # Eliminar espacios repetidos
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
