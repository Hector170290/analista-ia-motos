import sys
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Analista IA - Motos",
    page_icon="🏍️",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from pipeline.database import obtener_conexion


# ============================================================
# CARGAR DATOS
# ============================================================

def cargar_datos():

    conexion = obtener_conexion()

    consulta = """
        SELECT
            l.*,
            e.modelo_conversacion,
            e.modelos_alternativos,
            e.presupuesto,
            e.cuota_inicial,
            e.forma_pago,
            e.intencion_compra,
            e.objecion_principal,
            e.solicita_cotizacion,
            e.solicita_visita,
            e.resumen_conversacion,
            e.confianza_extraccion
        FROM leads l
        LEFT JOIN extracciones_ia e
            ON l.lead_id = e.lead_id
    """

    df = pd.read_sql_query(
        consulta,
        conexion
    )

    conexion.close()

    # ========================================================
    # NORMALIZAR CAMPOS PARA EL DASHBOARD
    # ========================================================

    if "canal" in df.columns:

        df["canal"] = (
            df["canal"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

    if "ciudad" in df.columns:

        df["ciudad"] = (
            df["ciudad"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

    return df


# ============================================================
# PRIORIDAD
# ============================================================

def calcular_prioridad(fila):

    if pd.isna(
        fila.get("modelo_homologado")
    ):
        return "PENDIENTE_MODELO"

    intencion = fila.get(
        "intencion_compra"
    )

    cotizacion = fila.get(
        "solicita_cotizacion"
    )

    visita = fila.get(
        "solicita_visita"
    )

    forma_pago = fila.get(
        "forma_pago"
    )

    cuota_inicial = fila.get(
        "cuota_inicial"
    )

    if intencion == "alta":
        return "ALTA"

    if cotizacion is True or cotizacion == 1:
        return "ALTA"

    if visita is True or visita == 1:
        return "ALTA"

    if intencion == "media":
        return "MEDIA"

    if forma_pago in [
        "contado",
        "financiado"
    ]:
        return "MEDIA"

    if pd.notna(
        cuota_inicial
    ):
        return "MEDIA"

    return "BAJA"


# ============================================================
# CARGA PRINCIPAL
# ============================================================

try:

    leads = cargar_datos()

except Exception as error:

    st.error(
        f"No fue posible cargar la base de datos: {error}"
    )

    st.stop()


# ============================================================
# CALCULAR PRIORIDAD
# ============================================================

leads["prioridad"] = leads.apply(
    calcular_prioridad,
    axis=1
)


# ============================================================
# FECHA DE GESTIÓN
# ============================================================

if "fecha_registro_normalizada" in leads.columns:

    leads["fecha_gestion"] = pd.to_datetime(
        leads["fecha_registro_normalizada"],
        errors="coerce"
    ).dt.date

else:

    leads["fecha_gestion"] = pd.NaT


# ============================================================
# ENCABEZADO
# ============================================================

st.title(
    "🏍️ Sistema Inteligente de Gestión de Leads"
)

st.write(
    "Priorización y asignación de leads comerciales "
    "mediante reglas de negocio e inteligencia artificial."
)


# ============================================================
# RESUMEN COMERCIAL
# ============================================================

st.subheader(
    "Resumen comercial"
)


total_leads = len(
    leads
)


total_clientes = (
    leads["cliente_id"]
    .nunique()
)


total_oportunidades = (
    leads["oportunidad_id"]
    .nunique()
)


leads_con_conversacion = int(
    leads["tiene_conversacion"]
    .fillna(0)
    .sum()
)


leads_procesados_ia = int(
    leads["confianza_extraccion"]
    .notna()
    .sum()
)


col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "Leads",
        total_leads
    )


with col2:

    st.metric(
        "Clientes",
        total_clientes
    )


with col3:

    st.metric(
        "Oportunidades",
        total_oportunidades
    )


with col4:

    st.metric(
        "Con conversación",
        leads_con_conversacion
    )


with col5:

    st.metric(
        "Procesados con IA",
        leads_procesados_ia
    )


# ============================================================
# PRIORIDADES
# ============================================================

st.subheader(
    "Prioridad de gestión"
)


prioridades = (
    leads["prioridad"]
    .value_counts()
    .reindex(
        [
            "ALTA",
            "MEDIA",
            "BAJA",
            "PENDIENTE_MODELO",
        ],
        fill_value=0,
    )
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "🔴 Alta",
        int(
            prioridades["ALTA"]
        )
    )


with col2:

    st.metric(
        "🟡 Media",
        int(
            prioridades["MEDIA"]
        )
    )


with col3:

    st.metric(
        "🟢 Baja",
        int(
            prioridades["BAJA"]
        )
    )


with col4:

    st.metric(
        "⚪ Pendiente modelo",
        int(
            prioridades[
                "PENDIENTE_MODELO"
            ]
        )
    )


# ============================================================
# FILTROS
# ============================================================

st.subheader(
    "Filtros de gestión"
)


col1, col2, col3, col4, col5 = st.columns(5)


# ============================================================
# EMPRESA
# ============================================================

with col1:

    empresas = [
        "Todas"
    ] + sorted(
        leads["empresa_id"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    empresa_seleccionada = st.selectbox(
        "Empresa",
        empresas
    )


# ============================================================
# PUNTO DE VENTA
# ============================================================

with col2:

    puntos = [
        "Todos"
    ] + sorted(
        leads["punto_venta_id"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    punto_seleccionado = st.selectbox(
        "Punto de venta",
        puntos
    )


# ============================================================
# ASESOR
# ============================================================

with col3:

    asesores = [
        "Todos"
    ] + sorted(
        leads["asesor_nombre"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    asesor_seleccionado = st.selectbox(
        "Asesor",
        asesores
    )


# ============================================================
# PRIORIDAD
# ============================================================

with col4:

    prioridades_filtro = [
        "Todas",
        "ALTA",
        "MEDIA",
        "BAJA",
        "PENDIENTE_MODELO",
    ]

    prioridad_seleccionada = st.selectbox(
        "Prioridad",
        prioridades_filtro
    )


# ============================================================
# CANAL
# ============================================================

with col5:

    canales = [
        "Todos"
    ] + sorted(
        leads["canal"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    canal_seleccionado = st.selectbox(
        "Canal",
        canales
    )


# ============================================================
# APLICAR FILTROS
# ============================================================

leads_filtrados = leads.copy()


if empresa_seleccionada != "Todas":

    leads_filtrados = leads_filtrados[
        leads_filtrados["empresa_id"]
        .astype(str)
        .str.strip()
        == empresa_seleccionada
    ]


if punto_seleccionado != "Todos":

    leads_filtrados = leads_filtrados[
        leads_filtrados["punto_venta_id"]
        .astype(str)
        .str.strip()
        == punto_seleccionado
    ]


if asesor_seleccionado != "Todos":

    leads_filtrados = leads_filtrados[
        leads_filtrados["asesor_nombre"]
        .astype(str)
        .str.strip()
        == asesor_seleccionado
    ]


if prioridad_seleccionada != "Todas":

    leads_filtrados = leads_filtrados[
        leads_filtrados["prioridad"]
        == prioridad_seleccionada
    ]


if canal_seleccionado != "Todos":

    leads_filtrados = leads_filtrados[
        leads_filtrados["canal"]
        == canal_seleccionado
    ]


# ============================================================
# ORDEN DE PRIORIDAD
# ============================================================

orden_prioridad = {
    "ALTA": 1,
    "MEDIA": 2,
    "BAJA": 3,
    "PENDIENTE_MODELO": 4,
}


leads_filtrados["orden_prioridad"] = (
    leads_filtrados["prioridad"]
    .map(orden_prioridad)
)


leads_filtrados = leads_filtrados.sort_values(
    by=[
        "orden_prioridad",
        "fecha_gestion",
    ],
    ascending=[
        True,
        False,
    ],
    na_position="last",
)


# ============================================================
# RESULTADO
# ============================================================

st.subheader(
    f"🔥 Lista priorizada de gestión "
    f"({len(leads_filtrados)} leads)"
)


# ============================================================
# TABLA DE GESTIÓN
# ============================================================

columnas_gestion = [
    "prioridad",
    "lead_id",
    "nombre_cliente",
    "telefono",
    "ciudad",
    "empresa_id",
    "punto_venta_id",
    "asesor_nombre",
    "fecha_gestion",
    "modelo_homologado",
    "modelo_conversacion",
    "intencion_compra",
    "forma_pago",
    "presupuesto",
    "cuota_inicial",
    "objecion_principal",
    "solicita_cotizacion",
    "solicita_visita",
    "resumen_conversacion",
]


columnas_gestion = [
    columna
    for columna in columnas_gestion
    if columna in leads_filtrados.columns
]


st.dataframe(
    leads_filtrados[
        columnas_gestion
    ],
    width="stretch",
    hide_index=True,
)


# ============================================================
# CALIDAD DE INFORMACIÓN
# ============================================================

st.subheader(
    "Calidad de información"
)


con_modelo = int(
    (
        leads_filtrados[
            "estado_modelo"
        ]
        == "HOMOLOGADO"
    ).sum()
)


sin_modelo = int(
    (
        leads_filtrados[
            "estado_modelo"
        ]
        != "HOMOLOGADO"
    ).sum()
)


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Modelo homologado",
        con_modelo
    )


with col2:

    st.metric(
        "Modelo pendiente/no identificado",
        sin_modelo
    )


with col3:

    if len(leads_filtrados) > 0:

        porcentaje = (
            con_modelo
            / len(leads_filtrados)
            * 100
        )

        st.metric(
            "% con modelo homologado",
            f"{porcentaje:.1f}%"
        )

    else:

        st.metric(
            "% con modelo homologado",
            "0.0%"
        )