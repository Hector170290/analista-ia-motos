import argparse

from pipeline.ingestion import cargar_fuentes
from pipeline.cleaning import limpiar_leads
from pipeline.deduplication import (
    eliminar_duplicados_lead,
    identificar_clientes,
)
from pipeline.opportunities import asignar_oportunidades
from pipeline.conversations import (
    preparar_conversaciones,
    unir_conversaciones,
)
from pipeline.ai_extraction import enriquecer_conversaciones


def ejecutar_pipeline(limite_ia=None):
    # 1. Cargar fuentes
    datos = cargar_fuentes()

    leads = datos["leads"]
    catalogo = datos["catalogo_motos"]

    # 2. Eliminar duplicados exactos
    leads = eliminar_duplicados_lead(leads)

    # 3. Limpiar y normalizar
    leads = limpiar_leads(leads, catalogo)

    # 4. Identificar clientes
    leads = identificar_clientes(leads)

    # 5. Identificar oportunidades
    leads = asignar_oportunidades(leads)

    # 6. Preparar conversaciones
    conversaciones = preparar_conversaciones(
        datos["conversaciones"]
    )

    # 7. Unir conversaciones con leads
    leads = unir_conversaciones(
        leads,
        conversaciones
    )

    # 8. Extraer información con IA
    if limite_ia is not None:
        leads = enriquecer_conversaciones(
            leads,
            limite=limite_ia
        )

    return leads, datos


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ia",
        type=int,
        default=None,
        help="Cantidad de conversaciones a procesar con IA"
    )

    args = parser.parse_args()

    resultado, datos = ejecutar_pipeline(
        limite_ia=args.ia
    )

    print("Pipeline ejecutado correctamente")
    print()
    print("Leads:", len(resultado))
    print("Clientes:", resultado["cliente_id"].nunique())
    print("Oportunidades:", resultado["oportunidad_id"].nunique())
    print(
        "Leads con conversación:",
        resultado["texto_conversacion"].notna().sum()
    )
    print(
        "Leads sin conversación:",
        resultado["texto_conversacion"].isna().sum()
    )

    if args.ia is not None:
        print(
            "Conversaciones procesadas con IA:",
            args.ia
        )

    print()
    print(resultado["estado_oportunidad"].value_counts())