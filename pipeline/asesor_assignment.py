import pandas as pd


ORDEN_PRIORIDAD = {
    "ALTA": 1,
    "MEDIA": 2,
    "BAJA": 3,
    "PENDIENTE_MODELO": 4,
}


def cargar_asesores(ruta):
    """
    Carga el archivo de asesores.
    """

    asesores = pd.read_csv(
        ruta,
        encoding="utf-8-sig"
    )

    asesores["activo"] = (
        asesores["activo"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    asesores["capacidad_diaria_leads"] = pd.to_numeric(
        asesores["capacidad_diaria_leads"],
        errors="coerce"
    ).fillna(0).astype(int)

    return asesores


def asignar_asesores(leads, asesores):
    """
    Asigna leads a asesores respetando:

    - Empresa
    - Punto de venta
    - Asesor activo
    - Capacidad diaria
    - Prioridad comercial

    La capacidad se reinicia cada día.
    """

    resultado = leads.copy()

    resultado["asesor_id"] = None
    resultado["asesor_nombre"] = None
    resultado["estado_asignacion"] = "SIN_ASIGNAR"

    if resultado.empty:
        return resultado

    # ========================================================
    # 1. FECHA DE ASIGNACIÓN
    # ========================================================

    # Usamos la fecha que ya fue normalizada
    # durante el proceso de limpieza.
    if "fecha_registro_normalizada" in resultado.columns:

        resultado["_fecha_asignacion"] = pd.to_datetime(
            resultado["fecha_registro_normalizada"],
            errors="coerce"
        ).dt.date

    elif "fecha_registro" in resultado.columns:

        # Respaldo por si la columna normalizada no existe.
        resultado["_fecha_asignacion"] = pd.to_datetime(
            resultado["fecha_registro"],
            errors="coerce",
            dayfirst=True
        ).dt.date

    else:

        resultado["_fecha_asignacion"] = None

    # ========================================================
    # 2. PRIORIDAD
    # ========================================================

    if "prioridad" not in resultado.columns:
        resultado["prioridad"] = "BAJA"

    resultado["_orden_prioridad"] = (
        resultado["prioridad"]
        .map(ORDEN_PRIORIDAD)
        .fillna(99)
    )

    # ========================================================
    # 3. ASESORES ACTIVOS
    # ========================================================

    asesores_activos = asesores[
        asesores["activo"] == "SI"
    ].copy()

    if asesores_activos.empty:
        return resultado

    # ========================================================
    # 4. PROCESAR CADA DÍA
    # ========================================================

    for fecha, indices_dia in resultado.groupby(
        "_fecha_asignacion",
        dropna=False
    ).groups.items():

        leads_dia = resultado.loc[
            indices_dia
        ].copy()

        # ----------------------------------------------------
        # Ordenar:
        # 1. ALTA
        # 2. MEDIA
        # 3. BAJA
        # 4. PENDIENTE_MODELO
        # ----------------------------------------------------

        columnas_orden = [
            "_orden_prioridad"
        ]

        if "fecha_registro_normalizada" in leads_dia.columns:
            columnas_orden.append(
                "fecha_registro_normalizada"
            )

        leads_dia = leads_dia.sort_values(
            by=columnas_orden,
            ascending=True,
            na_position="last"
        )

        # ====================================================
        # EMPRESA + PUNTO DE VENTA
        # ====================================================

        grupos = leads_dia.groupby(
            [
                "empresa_id",
                "punto_venta_id"
            ],
            dropna=False
        )

        for (
            empresa_id,
            punto_venta_id
        ), grupo in grupos:

            # ------------------------------------------------
            # Buscar asesores de esa empresa y punto de venta
            # ------------------------------------------------

            asesores_grupo = asesores_activos[
                (
                    asesores_activos["empresa_id"]
                    == empresa_id
                )
                &
                (
                    asesores_activos["punto_venta_id"]
                    == punto_venta_id
                )
            ].copy()

            if asesores_grupo.empty:
                continue

            # ------------------------------------------------
            # Capacidad disponible para ESTE día
            # ------------------------------------------------

            capacidad_restante = {
                fila["asesor_id"]:
                    int(fila["capacidad_diaria_leads"])
                for _, fila in asesores_grupo.iterrows()
            }

            nombres_asesores = {
                fila["asesor_id"]:
                    fila["nombre"]
                for _, fila in asesores_grupo.iterrows()
            }

            asesor_ids = list(
                capacidad_restante.keys()
            )

            posicion_asesor = 0

            # =================================================
            # ASIGNAR LEADS
            # =================================================

            for indice in grupo.index:

                asignado = False
                intentos = 0

                while (
                    intentos
                    < len(asesor_ids)
                ):

                    asesor_id = asesor_ids[
                        posicion_asesor
                        % len(asesor_ids)
                    ]

                    posicion_asesor += 1
                    intentos += 1

                    if (
                        capacidad_restante[
                            asesor_id
                        ]
                        <= 0
                    ):
                        continue

                    resultado.at[
                        indice,
                        "asesor_id"
                    ] = asesor_id

                    resultado.at[
                        indice,
                        "asesor_nombre"
                    ] = nombres_asesores[
                        asesor_id
                    ]

                    resultado.at[
                        indice,
                        "estado_asignacion"
                    ] = "ASIGNADO"

                    capacidad_restante[
                        asesor_id
                    ] -= 1

                    asignado = True

                    break

                if not asignado:
                    break

    # ========================================================
    # 5. LIMPIAR COLUMNAS AUXILIARES
    # ========================================================

    resultado = resultado.drop(
        columns=[
            "_fecha_asignacion",
            "_orden_prioridad"
        ],
        errors="ignore"
    )

    return resultado