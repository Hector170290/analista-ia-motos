import os
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
    layout="wide"
)


# ============================================================
# RUTA DEL PROYECTO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


# ============================================================
# BASE DE DATOS
# ============================================================

from pipeline.database import obtener_conexion


# ============================================================
# TÍTULO
# ============================================================

st.title("🏍️ Analista IA - Gestión de Leads")

st.caption(
    "Priorización y gestión comercial de leads de motocicletas"
)


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

    try:

        df = pd.read_sql_query(
            consulta,
            conexion
        )

    finally:

        conexion.close()

    return df


# ============================================================
# REGLAS DE PRIORIZACIÓN
# ============================================================

def calcular_prioridad(fila):

    modelo = fila.get(
        "modelo_homologado"
    )

    if pd.isna(modelo) or not str(modelo).strip():

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

    # --------------------------------------------------------
    # Normalizar valores
    # --------------------------------------------------------

    if isinstance(intencion, str):

        intencion = (
            intencion
            .strip()
            .lower()
        )

    if isinstance(forma_pago, str):

        forma_pago = (
            forma_pago
            .strip()
            .lower()
        )

    # --------------------------------------------------------
    # Convertir booleanos
    # --------------------------------------------------------

    if isinstance(cotizacion, str):

        cotizacion = (
            cotizacion
            .strip()
            .lower()
            in ["true", "1", "si", "sí", "yes"]
        )

    if isinstance(visita, str):

        visita = (
            visita
            .strip()
            .lower()
            in ["true", "1", "si", "sí", "yes"]
        )

    # --------------------------------------------------------
    # PRIORIDAD ALTA
    # --------------------------------------------------------

    if intencion == "alta":

        return "ALTA"

    if cotizacion is True:

        return "ALTA"

    if visita is True:

        return "ALTA"

    # --------------------------------------------------------
    # PRIORIDAD MEDIA
    # --------------------------------------------------------

    if intencion == "media":

        return "MEDIA"

    if forma_pago in [
        "contado",
        "financiado"
    ]:

        return "MEDIA"

    if pd.notna(cuota_inicial):

        return "MEDIA"

    # --------------------------------------------------------
    # PRIORIDAD BAJA
    # --------------------------------------------------------

    return "BAJA"


# ============================================================
# CARGAR INFORMACIÓN
# ============================================================

try:

    df = cargar_datos()

except Exception as error:

    st.error(
        f"No fue posible cargar la base de datos: {error}"
    )

    st.stop()


# ============================================================
# VALIDACIÓN
# ============================================================

if df.empty:

    st.warning(
        "La base de datos no contiene leads."
    )

    st.stop()


# ============================================================
# NORMALIZACIÓN PARA DASHBOARD
# ============================================================

for columna in [
    "canal",
    "ciudad",
    "empresa_id",
    "punto_venta_id",
    "asesor_nombre",
    "prioridad",
]:

    if columna in df.columns:

        df[columna] = (
            df[columna]
            .fillna("NO_INFORMADO")
            .astype(str)
            .str.strip()
            .str.upper()
        )


# ============================================================
# PRIORIDAD
# ============================================================

df["prioridad"] = df.apply(
    calcular_prioridad,
    axis=1
)


# ============================================================
# MÉTRICAS GENERALES
# ============================================================

total_leads = len(df)

total_clientes = (
    df["cliente_id"]
    .nunique()
    if "cliente_id" in df.columns
    else 0
)

total_oportunidades = (
    df["oportunidad_id"]
    .nunique()
    if "oportunidad_id" in df.columns
    else 0
)

if "tiene_conversacion" in df.columns:

    tiene_conversacion = (
        df["tiene_conversacion"]
        .fillna(False)
        .astype(bool)
        .sum()
    )

else:

    tiene_conversacion = 0


procesados_ia = (
    df["confianza_extraccion"]
    .notna()
    .sum()
    if "confianza_extraccion" in df.columns
    else 0
)


# ============================================================
# KPIs
# ============================================================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:

    st.metric(
        "Leads",
        f"{total_leads:,}"
    )

with col2:

    st.metric(
        "Clientes",
        f"{total_clientes:,}"
    )

with col3:

    st.metric(
        "Oportunidades",
        f"{total_oportunidades:,}"
    )

with col4:

    st.metric(
        "Con conversación",
        f"{tiene_conversacion:,}"
    )

with col5:

    st.metric(
        "Procesados con IA",
        f"{procesados_ia:,}"
    )


st.divider()


# ============================================================
# FILTROS
# ============================================================

st.subheader("Filtros de gestión")


col1, col2, col3, col4, col5 = st.columns(5)


# ------------------------------------------------------------
# EMPRESA
# ------------------------------------------------------------

with col1:

    empresas = sorted(
        df["empresa_id"]
        .dropna()
        .unique()
        .tolist()
    )

    empresas_filtro = st.multiselect(
        "Empresa",
        options=empresas,
        default=empresas
    )


# ------------------------------------------------------------
# PUNTO DE VENTA
# ------------------------------------------------------------

with col2:

    puntos = sorted(
        df["punto_venta_id"]
        .dropna()
        .unique()
        .tolist()
    )

    puntos_filtro = st.multiselect(
        "Punto de venta",
        options=puntos,
        default=puntos
    )


# ------------------------------------------------------------
# ASESOR
# ------------------------------------------------------------

with col3:

    asesores = sorted(
        df["asesor_nombre"]
        .dropna()
        .unique()
        .tolist()
    )

    asesores_filtro = st.multiselect(
        "Asesor",
        options=asesores,
        default=asesores
    )


# ------------------------------------------------------------
# PRIORIDAD
# ------------------------------------------------------------

with col4:

    prioridades = [
        "ALTA",
        "MEDIA",
        "BAJA",
        "PENDIENTE_MODELO"
    ]

    prioridades_filtro = st.multiselect(
        "Prioridad",
        options=prioridades,
        default=prioridades
    )


# ------------------------------------------------------------
# CANAL
# ------------------------------------------------------------

with col5:

    canales = sorted(
        df["canal"]
        .dropna()
        .unique()
        .tolist()
    )

    canales_filtro = st.multiselect(
        "Canal",
        options=canales,
        default=canales
    )


# ============================================================
# APLICAR FILTROS
# ============================================================

df_filtrado = df.copy()


if empresas_filtro:

    df_filtrado = df_filtrado[
        df_filtrado["empresa_id"].isin(
            empresas_filtro
        )
    ]


if puntos_filtro:

    df_filtrado = df_filtrado[
        df_filtrado["punto_venta_id"].isin(
            puntos_filtro
        )
    ]


if asesores_filtro:

    df_filtrado = df_filtrado[
        df_filtrado["asesor_nombre"].isin(
            asesores_filtro
        )
    ]


if prioridades_filtro:

    df_filtrado = df_filtrado[
        df_filtrado["prioridad"].isin(
            prioridades_filtro
        )
    ]


if canales_filtro:

    df_filtrado = df_filtrado[
        df_filtrado["canal"].isin(
            canales_filtro
        )
    ]


# ============================================================
# RESUMEN DE PRIORIDADES
# ============================================================

st.subheader("Distribución de prioridades")


prioridades_resumen = (
    df_filtrado["prioridad"]
    .value_counts()
    .reindex(
        [
            "ALTA",
            "MEDIA",
            "BAJA",
            "PENDIENTE_MODELO"
        ],
        fill_value=0
    )
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "🔴 Alta",
        int(
            prioridades_resumen["ALTA"]
        )
    )


with c2:

    st.metric(
        "🟠 Media",
        int(
            prioridades_resumen["MEDIA"]
        )
    )


with c3:

    st.metric(
        "🟡 Baja",
        int(
            prioridades_resumen["BAJA"]
        )
    )


with c4:

    st.metric(
        "⚪ Pendiente modelo",
        int(
            prioridades_resumen[
                "PENDIENTE_MODELO"
            ]
        )
    )


st.divider()


# ============================================================
# LISTA DE GESTIÓN
# ============================================================

st.subheader(
    "📋 Leads priorizados para gestión"
)


# ------------------------------------------------------------
# ORDEN
# ------------------------------------------------------------

orden_prioridad = {
    "ALTA": 1,
    "MEDIA": 2,
    "BAJA": 3,
    "PENDIENTE_MODELO": 4
}


df_filtrado["_orden_prioridad"] = (
    df_filtrado["prioridad"]
    .map(orden_prioridad)
    .fillna(99)
)


if "fecha_registro_normalizada" in df_filtrado.columns:

    df_filtrado[
        "_fecha_orden"
    ] = pd.to_datetime(
        df_filtrado[
            "fecha_registro_normalizada"
        ],
        errors="coerce"
    )

else:

    df_filtrado["_fecha_orden"] = pd.NaT


df_filtrado = (
    df_filtrado
    .sort_values(
        by=[
            "_orden_prioridad",
            "_fecha_orden"
        ],
        ascending=[
            True,
            True
        ],
        na_position="last"
    )
)


# ============================================================
# TABLA PRINCIPAL
# ============================================================

columnas_tabla = [
    "lead_id",
    "cliente_id",
    "oportunidad_id",
    "fecha_registro",
    "canal",
    "empresa_id",
    "punto_venta_id",
    "nombre_cliente",
    "telefono",
    "ciudad",
    "modelo_interes_texto",
    "modelo_homologado",
    "modelo_conversacion",
    "intencion_compra",
    "forma_pago",
    "cuota_inicial",
    "solicita_cotizacion",
    "solicita_visita",
    "objecion_principal",
    "prioridad",
    "asesor_nombre",
    "estado_asignacion",
]


columnas_disponibles = [
    columna
    for columna in columnas_tabla
    if columna in df_filtrado.columns
]


tabla = df_filtrado[
    columnas_disponibles
].copy()


# ============================================================
# NOMBRES MÁS AMIGABLES
# ============================================================

renombrar = {

    "lead_id": "Lead",

    "cliente_id": "Cliente",

    "oportunidad_id": "Oportunidad",

    "fecha_registro": "Fecha registro",

    "canal": "Canal",

    "empresa_id": "Empresa",

    "punto_venta_id": "Punto venta",

    "nombre_cliente": "Cliente nombre",

    "telefono": "Teléfono",

    "ciudad": "Ciudad",

    "modelo_interes_texto": "Modelo informado",

    "modelo_homologado": "Modelo homologado",

    "modelo_conversacion": "Modelo conversación",

    "intencion_compra": "Intención",

    "forma_pago": "Forma de pago",

    "cuota_inicial": "Cuota inicial",

    "solicita_cotizacion": "Solicita cotización",

    "solicita_visita": "Solicita visita",

    "objecion_principal": "Objeción",

    "prioridad": "Prioridad",

    "asesor_nombre": "Asesor",

    "estado_asignacion": "Asignación",
}


tabla = tabla.rename(
    columns=renombrar
)


# ============================================================
# MOSTRAR TABLA
# ============================================================

st.dataframe(
    tabla,
    use_container_width=True,
    hide_index=True
)


st.caption(
    f"Mostrando {len(tabla):,} leads de {total_leads:,} registros."
)


# ============================================================
# INFORMACIÓN DE CALIDAD
# ============================================================

st.divider()

st.subheader(
    "🔎 Información de calidad de los datos"
)


# ------------------------------------------------------------
# MODELOS
# ------------------------------------------------------------

if "estado_modelo" in df_filtrado.columns:

    modelos_no_identificados = (
        df_filtrado[
            df_filtrado[
                "estado_modelo"
            ] != "HOMOLOGADO"
        ]
        .shape[0]
    )

else:

    modelos_no_identificados = 0


# ------------------------------------------------------------
# CONVERSACIONES
# ------------------------------------------------------------

leads_sin_conversacion = (
    total_leads
    - tiene_conversacion
)


# ------------------------------------------------------------
# ASIGNACIÓN
# ------------------------------------------------------------

if "estado_asignacion" in df_filtrado.columns:

    sin_asignar = (
        df_filtrado[
            df_filtrado[
                "estado_asignacion"
            ]
            != "ASIGNADO"
        ]
        .shape[0]
    )

else:

    sin_asignar = 0


q1, q2, q3 = st.columns(3)


with q1:

    st.metric(
        "Modelo no identificado",
        f"{modelos_no_identificados:,}"
    )


with q2:

    st.metric(
        "Leads sin conversación",
        f"{leads_sin_conversacion:,}"
    )


with q3:

    st.metric(
        "Leads sin asignar",
        f"{sin_asignar:,}"
    )


# ============================================================
# CALIDAD POR ASESOR
# ============================================================

st.subheader(
    "Calidad de información por asesor"
)


if (
    "asesor_nombre" in df_filtrado.columns
    and "estado_modelo" in df_filtrado.columns
):

    calidad_asesor = (
        df_filtrado
        .assign(
            modelo_incompleto=
            df_filtrado[
                "estado_modelo"
            ]
            != "HOMOLOGADO"
        )
        .groupby(
            "asesor_nombre",
            dropna=False
        )
        .agg(
            leads=(
                "lead_id",
                "count"
            ),
            modelos_incompletos=(
                "modelo_incompleto",
                "sum"
            )
        )
        .reset_index()
    )

    calidad_asesor[
        "incidencia_modelo_%"
    ] = (
        calidad_asesor[
            "modelos_incompletos"
        ]
        / calidad_asesor["leads"]
        * 100
    ).round(1)

    calidad_asesor = (
        calidad_asesor
        .sort_values(
            "incidencia_modelo_%",
            ascending=False
        )
    )

    calidad_asesor = calidad_asesor.rename(
        columns={
            "asesor_nombre": "Asesor",
            "leads": "Leads",
            "modelos_incompletos":
                "Modelos incompletos",
            "incidencia_modelo_%":
                "Incidencia modelo (%)"
        }
    )

    st.dataframe(
        calidad_asesor,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info(
        "No hay información suficiente para calcular "
        "la calidad por asesor."
    )


# ============================================================
# DETALLE DE UN LEAD
# ============================================================

st.divider()

st.subheader(
    "🔍 Detalle de lead"
)


if not df_filtrado.empty:

    leads_disponibles = (
        df_filtrado[
            "lead_id"
        ]
        .astype(str)
        .tolist()
    )

    lead_seleccionado = st.selectbox(
        "Seleccione un lead",
        options=leads_disponibles
    )

    detalle = df_filtrado[
        df_filtrado[
            "lead_id"
        ].astype(str)
        == str(lead_seleccionado)
    ]

    if not detalle.empty:

        fila = detalle.iloc[0]

        c1, c2, c3 = st.columns(3)

        with c1:

            st.write(
                "**Lead:**",
                fila.get(
                    "lead_id",
                    ""
                )
            )

            st.write(
                "**Cliente:**",
                fila.get(
                    "nombre_cliente",
                    ""
                )
            )

            st.write(
                "**Teléfono:**",
                fila.get(
                    "telefono",
                    ""
                )
            )

            st.write(
                "**Ciudad:**",
                fila.get(
                    "ciudad",
                    ""
                )
            )

        with c2:

            st.write(
                "**Modelo informado:**",
                fila.get(
                    "modelo_interes_texto",
                    ""
                )
            )

            st.write(
                "**Modelo homologado:**",
                fila.get(
                    "modelo_homologado",
                    ""
                )
            )

            st.write(
                "**Modelo conversación:**",
                fila.get(
                    "modelo_conversacion",
                    ""
                )
            )

            st.write(
                "**Prioridad:**",
                fila.get(
                    "prioridad",
                    ""
                )
            )

        with c3:

            st.write(
                "**Intención:**",
                fila.get(
                    "intencion_compra",
                    ""
                )
            )

            st.write(
                "**Forma de pago:**",
                fila.get(
                    "forma_pago",
                    ""
                )
            )

            st.write(
                "**Cuota inicial:**",
                fila.get(
                    "cuota_inicial",
                    ""
                )
            )

            st.write(
                "**Asesor:**",
                fila.get(
                    "asesor_nombre",
                    ""
                )
            )

        st.markdown(
            "---"
        )

        st.write(
            "**Objeción principal:**"
        )

        st.write(
            fila.get(
                "objecion_principal",
                None
            )
            or "No identificada"
        )

        st.write(
            "**Resumen de conversación:**"
        )

        st.write(
            fila.get(
                "resumen_conversacion",
                None
            )
            or "No disponible"
        )


# ============================================================
# LIMPIEZA INTERNA
# ============================================================

df_filtrado = df_filtrado.drop(
    columns=[
        "_orden_prioridad",
        "_fecha_orden"
    ],
    errors="ignore"
)