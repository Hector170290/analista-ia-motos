from pathlib import Path
import pandas as pd
import json


# Directorio donde están las fuentes de datos
DATA_DIR = Path(__file__).resolve().parent.parent


FUENTES = {
    "leads": "leads.csv",
    "conversaciones": "conversaciones.json",
    "catalogo_motos": "catalogo_motos.csv",
    "asesores": "asesores.csv",
    "historico_cierres": "historico_cierres.csv",
}


def cargar_fuentes():
    datos = {}

    for nombre, archivo in FUENTES.items():
        ruta = DATA_DIR / archivo

        if not ruta.exists():
            raise FileNotFoundError(
                f"No se encontró la fuente: {ruta}"
            )

        if ruta.suffix.lower() == ".csv":
            datos[nombre] = pd.read_csv(ruta)

        elif ruta.suffix.lower() == ".json":
            with open(ruta, "r", encoding="utf-8") as f:
                datos[nombre] = json.load(f)

    return datos
    