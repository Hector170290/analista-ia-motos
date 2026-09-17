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


def ejecutar_pipeline():
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

    # 7. Unir conversaciones con los leads
    leads = unir_conversaciones(
        leads,
        conversaciones
    )

    return leads, datos


if __name__ == "__main__":
    resultado, datos = ejecutar_pipeline()

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
    print()
    print(resultado["estado_oportunidad"].value_counts())