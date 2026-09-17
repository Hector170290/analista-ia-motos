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
from pipeline.asesor_assignment import (
    cargar_asesores,
    asignar_asesores,
)
from pipeline.database import (
    crear_tablas,
    guardar_leads,
    guardar_extracciones_ia,
    cargar_extracciones_ia,
)


def integrar_extracciones_ia(leads, extracciones_ia):
    """
    Une las extracciones de IA almacenadas en la base
    con el conjunto actual de leads.

    No realiza nuevas llamadas a la API.
    """

    if extracciones_ia.empty:
        return leads

    columnas_ia = [
        "modelo_conversacion",
        "modelos_alternativos",
        "presupuesto",
        "cuota_inicial",
        "forma_pago",
        "intencion_compra",
        "objecion_principal",
        "solicita_cotizacion",
        "solicita_visita",
        "resumen_conversacion",
        "confianza_extraccion",
    ]

    extracciones = extracciones_ia[
        ["lead_id", *columnas_ia]
    ].copy()

    # Si alguna columna no existe, crearla
    for columna in columnas_ia:

        if columna not in leads.columns:
            leads[columna] = None

    # Eliminar columnas IA actuales antes del merge
    leads = leads.drop(
        columns=columnas_ia,
        errors="ignore"
    )

    leads = leads.merge(
        extracciones,
        on="lead_id",
        how="left"
    )

    return leads


def ejecutar_pipeline(limite_ia=None):
    """
    Ejecuta el pipeline completo de procesamiento de leads.

    Flujo:
    1. Carga de fuentes
    2. Eliminación de duplicados
    3. Limpieza y normalización
    4. Identificación de clientes
    5. Identificación de oportunidades
    6. Integración de conversaciones
    7. Extracción de IA nueva, si corresponde
    8. Recuperación de IA existente
    9. Priorización
    10. Asignación de asesores
    11. Persistencia
    """

    # ========================================================
    # 1. CREAR TABLAS
    # ========================================================

    crear_tablas()

    # ========================================================
    # 2. CARGAR FUENTES
    # ========================================================

    datos = cargar_fuentes()

    leads = datos["leads"]
    catalogo = datos["catalogo_motos"]

    # ========================================================
    # 3. ELIMINAR DUPLICADOS EXACTOS
    # ========================================================

    leads = eliminar_duplicados_lead(
        leads
    )

    # ========================================================
    # 4. LIMPIAR Y NORMALIZAR
    # ========================================================

    leads = limpiar_leads(
        leads,
        catalogo
    )

    # ========================================================
    # 5. IDENTIFICAR CLIENTES
    # ========================================================

    leads = identificar_clientes(
        leads
    )

    # ========================================================
    # 6. IDENTIFICAR OPORTUNIDADES
    # ========================================================

    leads = asignar_oportunidades(
        leads
    )

    # ========================================================
    # 7. PREPARAR CONVERSACIONES
    # ========================================================

    conversaciones = preparar_conversaciones(
        datos["conversaciones"]
    )

    # ========================================================
    # 8. UNIR CONVERSACIONES
    # ========================================================

    leads = unir_conversaciones(
        leads,
        conversaciones
    )

    leads["tiene_conversacion"] = (
        leads["texto_conversacion"].notna()
    )

    # ========================================================
    # 9. PROCESAR IA NUEVA
    # ========================================================

    if limite_ia is not None:

        leads = enriquecer_conversaciones(
            leads,
            limite=limite_ia
        )

    # ========================================================
    # 10. RECUPERAR IA EXISTENTE
    # ========================================================

    extracciones_ia = cargar_extracciones_ia()

    leads = integrar_extracciones_ia(
        leads,
        extracciones_ia
    )

    # ========================================================
    # 11. PRIORIZAR
    # ========================================================

    leads = aplicar_priorizacion(
        leads
    )

    # ========================================================
    # 12. ORDENAR POR PRIORIDAD
    # ========================================================

    orden_prioridad = {
        "ALTA": 1,
        "MEDIA": 2,
        "BAJA": 3,
        "PENDIENTE_MODELO": 4,
    }

    leads["orden_prioridad"] = (
        leads["prioridad"]
        .map(orden_prioridad)
    )

    leads = leads.sort_values(
        by=[
            "orden_prioridad",
            "fecha_registro"
        ],
        ascending=[
            True,
            True
        ],
        na_position="last"
    )

    leads = leads.drop(
        columns="orden_prioridad"
    )

    # ========================================================
    # 13. CARGAR ASESORES
    # ========================================================

    asesores = cargar_asesores(
        "asesores.csv"
    )

    # ========================================================
    # 14. ASIGNAR ASESORES
    # ========================================================

    leads = asignar_asesores(
        leads,
        asesores
    )

    # ========================================================
    # 15. GUARDAR LEADS
    # ========================================================

    guardar_leads(
        leads
    )

    # ========================================================
    # 16. GUARDAR EXTRACCIONES IA
    # ========================================================

    if limite_ia is not None:

        guardar_extracciones_ia(
            leads
        )

    return leads, datos


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--ia",
        type=int,
        default=None,
        help="Cantidad de conversaciones nuevas a procesar con IA"
    )

    args = parser.parse_args()

    resultado, datos = ejecutar_pipeline(
        limite_ia=args.ia
    )

    print(
        "Pipeline ejecutado correctamente"
    )

    print()

    print(
        "Leads:",
        len(resultado)
    )

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

    # ========================================================
    # IA
    # ========================================================

    print()

    print(
        "Extracciones IA disponibles:",
        resultado["confianza_extraccion"].notna().sum()
    )

    print()

    print(
        "Distribución de prioridades:"
    )

    print(
        resultado["prioridad"].value_counts(
            dropna=False
        )
    )

    # ========================================================
    # ASESORES
    # ========================================================

    print()

    print(
        "Distribución de asignación:"
    )

    print(
        resultado["estado_asignacion"].value_counts(
            dropna=False
        )
    )

    print()

    print(
        "Leads por asesor:"
    )

    asignados = resultado[
        resultado["estado_asignacion"] == "ASIGNADO"
    ]

    if not asignados.empty:

        print(
            asignados[
                [
                    "asesor_id",
                    "asesor_nombre"
                ]
            ].value_counts()
        )

    # ========================================================
    # OPORTUNIDADES
    # ========================================================

    print()

    print(
        "Estado de oportunidades:"
    )

    print(
        resultado["estado_oportunidad"].value_counts()
    )

    print()

    print(
        "Base de datos actualizada correctamente."
    )