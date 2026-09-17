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
from pipeline.prioritization import aplicar_priorizacion


def ejecutar_pipeline(limite_ia=None):
    """
    Ejecuta el pipeline completo de procesamiento de leads.

    Flujo:
    1. Carga de fuentes
    2. Eliminación de duplicados de lead
    3. Limpieza y normalización
    4. Identificación de clientes
    5. Identificación de oportunidades
    6. Integración de conversaciones
    7. Extracción de información con IA
    8. Priorización comercial
    """

    # 1. Cargar fuentes
    datos = cargar_fuentes()

    leads = datos["leads"]
    catalogo = datos["catalogo_motos"]

    # 2. Eliminar duplicados exactos de lead
    leads = eliminar_duplicados_lead(leads)

    # 3. Limpiar y normalizar leads
    leads = limpiar_leads(leads, catalogo)

    # 4. Identificar clientes
    leads = identificar_clientes(leads)

    # 5. Asignar oportunidades
    leads = asignar_oportunidades(leads)

    # 6. Preparar y unir conversaciones
    conversaciones = preparar_conversaciones(
        datos["conversaciones"]
    )

    leads = unir_conversaciones(
        leads,
        conversaciones
    )

    # 7. Procesar conversaciones con IA
    if limite_ia is not None:

        leads = enriquecer_conversaciones(
            leads,
            limite=limite_ia
        )

        # 8. Aplicar priorización
        leads = aplicar_priorizacion(leads)

        # 9. Ordenar resultados por prioridad
        orden_prioridad = {
            "ALTA": 1,
            "MEDIA": 2,
            "BAJA": 3,
            "PENDIENTE_MODELO": 4,
        }

        leads["orden_prioridad"] = (
            leads["prioridad"].map(orden_prioridad)
        )

        leads = leads.sort_values(
            "orden_prioridad"
        ).drop(
            columns="orden_prioridad"
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

    print(
        "Clientes:",
        resultado["cliente_id"].nunique()
    )

    print(
        "Oportunidades:",
        resultado["oportunidad_id"].nunique()
    )

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
        print("Distribución de prioridades:")

        print(
            resultado["prioridad"].value_counts(
                dropna=False
            )
        )

    print()

    print("Estado de oportunidades:")

    print(
        resultado["estado_oportunidad"].value_counts()
    )