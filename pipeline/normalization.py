import re
import unicodedata
from datetime import datetime


def normalizar_texto(valor):
    """
    Normaliza texto para facilitar comparaciones.
    """
    if valor is None:
        return None

    texto = str(valor).strip().lower()

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto


def normalizar_telefono(valor):
    """
    Conserva únicamente los dígitos del teléfono.
    """
    if valor is None:
        return None

    telefono = re.sub(r"\D", "", str(valor))

    return telefono if telefono else None


def normalizar_dataframe(
    df,
    columnas_texto=None,
    columna_telefono=None
):
    """
    Aplica normalización básica a un DataFrame.
    """

    df = df.copy()

    if columnas_texto:
        for columna in columnas_texto:
            if columna in df.columns:
                df[f"{columna}_normalizado"] = (
                    df[columna].apply(normalizar_texto)
                )

    if columna_telefono and columna_telefono in df.columns:
        df[f"{columna_telefono}_normalizado"] = (
            df[columna_telefono].apply(normalizar_telefono)
        )

    return df


def normalizar_fecha(valor):
    """
    Convierte diferentes formatos comunes de fecha
    a un objeto datetime.
    """

    if valor is None:
        return None

    texto = str(valor).strip()

    formatos = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
    ]

    for formato in formatos:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue

    return None


def normalizar_ciudad(valor):
    """
    Normaliza nombres de ciudades para facilitar comparaciones.
    """

    ciudad = normalizar_texto(valor)

    if ciudad is None:
        return None

    equivalencias = {
        "bogota": "bogota",
        "bogota d.c.": "bogota",
        "bogota dc": "bogota",
        "medellin": "medellin",
        "cartagena": "cartagena",
        "barranquilla": "barranquilla",
        "santa marta": "santa marta",
        "monteria": "monteria",
        "bello": "bello",
        "soacha": "soacha",
        "itagui": "itagui",
        "rionegro": "rionegro",
        "soledad": "soledad",
    }

    return equivalencias.get(ciudad, ciudad)


def normalizar_modelo(valor):
    """
    Limpia el texto del modelo para facilitar su homologación.
    No intenta identificar un modelo que no esté explícitamente indicado.
    """

    modelo = normalizar_texto(valor)

    if modelo is None:
        return None

    modelo = re.sub(r"\s+", " ", modelo)

    modelo = modelo.replace("-", " ")
    modelo = modelo.replace("_", " ")

    modelo = re.sub(r"\s+", " ", modelo).strip()

    return modelo
