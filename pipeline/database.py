import json
import os
import sqlite3
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SQLITE_PATH = BASE_DIR / "data" / "motos.db"

load_dotenv()


# ============================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================

def obtener_database_url():
    """
    Obtiene la URL de PostgreSQL/Supabase en el momento
    en que se necesita.

    Esto permite utilizar:
    - .env en entorno local
    - Streamlit Secrets en producción
    """

    return os.getenv("DATABASE_URL")


def usa_postgresql():
    """
    Determina si debemos utilizar PostgreSQL/Supabase.
    """

    return bool(obtener_database_url())


# ============================================================
# CONEXIÓN
# ============================================================

def obtener_conexion():

    database_url = obtener_database_url()

    # --------------------------------------------------------
    # PostgreSQL / Supabase
    # --------------------------------------------------------

    if database_url:

        return psycopg.connect(
            database_url,
            sslmode="require"
        )

    # --------------------------------------------------------
    # SQLite local
    # --------------------------------------------------------

    SQLITE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    return sqlite3.connect(
        SQLITE_PATH
    )


# ============================================================
# CREAR TABLAS
# ============================================================

def crear_tablas():

    # ========================================================
    # PostgreSQL / Supabase
    # ========================================================

    if usa_postgresql():

        conexion = obtener_conexion()

        cursor = conexion.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                lead_id TEXT PRIMARY KEY,
                cliente_id TEXT,
                oportunidad_id TEXT,
                fecha_registro TEXT,
                fecha_registro_normalizada TIMESTAMP,
                fecha_primer_contacto TEXT,
                canal TEXT,
                empresa_id TEXT,
                punto_venta_id TEXT,
                nombre_cliente TEXT,
                telefono TEXT,
                email TEXT,
                ciudad TEXT,
                modelo_interes_texto TEXT,
                modelo_homologado TEXT,
                estado_modelo TEXT,
                estado_oportunidad TEXT,
                tiene_conversacion BOOLEAN,
                asesor_id TEXT,
                asesor_nombre TEXT,
                estado_asignacion TEXT,
                prioridad TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS extracciones_ia (
                lead_id TEXT PRIMARY KEY,
                modelo_conversacion TEXT,
                modelos_alternativos JSONB,
                presupuesto TEXT,
                cuota_inicial TEXT,
                forma_pago TEXT,
                intencion_compra TEXT,
                objecion_principal TEXT,
                solicita_cotizacion BOOLEAN,
                solicita_visita BOOLEAN,
                resumen_conversacion TEXT,
                confianza_extraccion REAL,
                FOREIGN KEY (lead_id)
                    REFERENCES leads(lead_id)
            )
            """
        )

        conexion.commit()

        conexion.close()

        return

    # ========================================================
    # SQLite local
    # ========================================================

    conexion = obtener_conexion()

    cursor = conexion.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            lead_id TEXT PRIMARY KEY,
            cliente_id TEXT,
            oportunidad_id TEXT,
            fecha_registro TEXT,
            fecha_registro_normalizada TEXT,
            fecha_primer_contacto TEXT,
            canal TEXT,
            empresa_id TEXT,
            punto_venta_id TEXT,
            nombre_cliente TEXT,
            telefono TEXT,
            email TEXT,
            ciudad TEXT,
            modelo_interes_texto TEXT,
            modelo_homologado TEXT,
            estado_modelo TEXT,
            estado_oportunidad TEXT,
            tiene_conversacion INTEGER,
            asesor_id TEXT,
            asesor_nombre TEXT,
            estado_asignacion TEXT,
            prioridad TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS extracciones_ia (
            lead_id TEXT PRIMARY KEY,
            modelo_conversacion TEXT,
            modelos_alternativos TEXT,
            presupuesto TEXT,
            cuota_inicial TEXT,
            forma_pago TEXT,
            intencion_compra TEXT,
            objecion_principal TEXT,
            solicita_cotizacion INTEGER,
            solicita_visita INTEGER,
            resumen_conversacion TEXT,
            confianza_extraccion REAL,
            FOREIGN KEY (lead_id)
                REFERENCES leads(lead_id)
        )
        """
    )

    conexion.commit()

    conexion.close()


# ============================================================
# CONVERTIR BOOLEANOS
# ============================================================

def convertir_booleano(valor):

    if valor is None:
        return None

    try:

        if pd.isna(valor):
            return None

    except (
        TypeError,
        ValueError
    ):

        pass

    if isinstance(valor, str):

        valor_normalizado = (
            valor
            .strip()
            .lower()
        )

        if valor_normalizado in [
            "true",
            "1",
            "si",
            "sí",
            "yes"
        ]:
            return True

        if valor_normalizado in [
            "false",
            "0",
            "no"
        ]:
            return False

    return bool(valor)


# ============================================================
# GUARDAR LEADS
# ============================================================

def guardar_leads(df):

    columnas = [
        "lead_id",
        "cliente_id",
        "oportunidad_id",
        "fecha_registro",
        "fecha_registro_normalizada",
        "fecha_primer_contacto",
        "canal",
        "empresa_id",
        "punto_venta_id",
        "nombre_cliente",
        "telefono",
        "email",
        "ciudad",
        "modelo_interes_texto",
        "modelo_homologado",
        "estado_modelo",
        "estado_oportunidad",
        "tiene_conversacion",
        "asesor_id",
        "asesor_nombre",
        "estado_asignacion",
        "prioridad",
    ]

    datos = df.copy()

    for columna in columnas:

        if columna not in datos.columns:
            datos[columna] = None

    datos = datos[columnas]

    # ========================================================
    # POSTGRESQL
    # ========================================================

    if usa_postgresql():

        sql = """
            INSERT INTO leads (
                lead_id,
                cliente_id,
                oportunidad_id,
                fecha_registro,
                fecha_registro_normalizada,
                fecha_primer_contacto,
                canal,
                empresa_id,
                punto_venta_id,
                nombre_cliente,
                telefono,
                email,
                ciudad,
                modelo_interes_texto,
                modelo_homologado,
                estado_modelo,
                estado_oportunidad,
                tiene_conversacion,
                asesor_id,
                asesor_nombre,
                estado_asignacion,
                prioridad
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (lead_id)
            DO UPDATE SET
                cliente_id = EXCLUDED.cliente_id,
                oportunidad_id = EXCLUDED.oportunidad_id,
                fecha_registro = EXCLUDED.fecha_registro,
                fecha_registro_normalizada =
                    EXCLUDED.fecha_registro_normalizada,
                fecha_primer_contacto =
                    EXCLUDED.fecha_primer_contacto,
                canal = EXCLUDED.canal,
                empresa_id = EXCLUDED.empresa_id,
                punto_venta_id = EXCLUDED.punto_venta_id,
                nombre_cliente = EXCLUDED.nombre_cliente,
                telefono = EXCLUDED.telefono,
                email = EXCLUDED.email,
                ciudad = EXCLUDED.ciudad,
                modelo_interes_texto =
                    EXCLUDED.modelo_interes_texto,
                modelo_homologado =
                    EXCLUDED.modelo_homologado,
                estado_modelo =
                    EXCLUDED.estado_modelo,
                estado_oportunidad =
                    EXCLUDED.estado_oportunidad,
                tiene_conversacion =
                    EXCLUDED.tiene_conversacion,
                asesor_id = EXCLUDED.asesor_id,
                asesor_nombre = EXCLUDED.asesor_nombre,
                estado_asignacion =
                    EXCLUDED.estado_asignacion,
                prioridad = EXCLUDED.prioridad
        """

        registros = []

        for _, fila in datos.iterrows():

            # ------------------------------------------------
            # Fecha
            # ------------------------------------------------

            fecha = pd.to_datetime(
                fila["fecha_registro_normalizada"],
                errors="coerce"
            )

            if pd.isna(fecha):

                fecha = None

            else:

                fecha = fecha.to_pydatetime()

            # ------------------------------------------------
            # Booleano
            # ------------------------------------------------

            tiene_conversacion = convertir_booleano(
                fila["tiene_conversacion"]
            )

            # ------------------------------------------------
            # Convertir NaN a None
            # ------------------------------------------------

            valores = []

            for columna in columnas:

                if columna == "fecha_registro_normalizada":

                    valores.append(fecha)

                elif columna == "tiene_conversacion":

                    valores.append(
                        tiene_conversacion
                    )

                else:

                    valor = fila[columna]

                    try:

                        if pd.isna(valor):
                            valor = None

                    except (
                        TypeError,
                        ValueError
                    ):

                        pass

                    valores.append(valor)

            registros.append(
                tuple(valores)
            )

        conexion = obtener_conexion()

        with conexion.cursor() as cursor:

            cursor.executemany(
                sql,
                registros
            )

        conexion.commit()

        conexion.close()

        return

    # ========================================================
    # SQLITE
    # ========================================================

    datos[
        "fecha_registro_normalizada"
    ] = datos[
        "fecha_registro_normalizada"
    ].apply(
        lambda x: (
            x.isoformat()
            if hasattr(x, "isoformat")
            else x
        )
    )

    conexion = obtener_conexion()

    cursor = conexion.cursor()

    cursor.execute(
        "DELETE FROM leads"
    )

    placeholders = ",".join(
        ["?"] * len(columnas)
    )

    sql = f"""
        INSERT INTO leads (
            {",".join(columnas)}
        )
        VALUES (
            {placeholders}
        )
    """

    registros = [
        tuple(fila)
        for fila in datos.itertuples(
            index=False,
            name=None
        )
    ]

    cursor.executemany(
        sql,
        registros
    )

    conexion.commit()

    conexion.close()


# ============================================================
# GUARDAR EXTRACCIONES IA
# ============================================================

def guardar_extracciones_ia(df):

    columnas = [
        "lead_id",
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

    datos = df.copy()

    if "confianza_extraccion" not in datos.columns:
        return

    datos = datos[
        datos["confianza_extraccion"].notna()
    ].copy()

    if datos.empty:
        return

    for columna in columnas:

        if columna not in datos.columns:
            datos[columna] = None

    datos = datos[columnas]

    # ========================================================
    # POSTGRESQL
    # ========================================================

    if usa_postgresql():

        sql = """
            INSERT INTO extracciones_ia (
                lead_id,
                modelo_conversacion,
                modelos_alternativos,
                presupuesto,
                cuota_inicial,
                forma_pago,
                intencion_compra,
                objecion_principal,
                solicita_cotizacion,
                solicita_visita,
                resumen_conversacion,
                confianza_extraccion
            )
            VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (lead_id)
            DO UPDATE SET
                modelo_conversacion =
                    EXCLUDED.modelo_conversacion,
                modelos_alternativos =
                    EXCLUDED.modelos_alternativos,
                presupuesto =
                    EXCLUDED.presupuesto,
                cuota_inicial =
                    EXCLUDED.cuota_inicial,
                forma_pago =
                    EXCLUDED.forma_pago,
                intencion_compra =
                    EXCLUDED.intencion_compra,
                objecion_principal =
                    EXCLUDED.objecion_principal,
                solicita_cotizacion =
                    EXCLUDED.solicita_cotizacion,
                solicita_visita =
                    EXCLUDED.solicita_visita,
                resumen_conversacion =
                    EXCLUDED.resumen_conversacion,
                confianza_extraccion =
                    EXCLUDED.confianza_extraccion
        """

        registros = []

        for _, fila in datos.iterrows():

            modelos = fila[
                "modelos_alternativos"
            ]

            # ------------------------------------------------
            # Convertir modelos alternativos a JSON válido
            # ------------------------------------------------

            if modelos is None:

                modelos_json = None

            else:

                try:

                    if pd.isna(modelos):

                        modelos_json = None

                    else:

                        if isinstance(
                            modelos,
                            str
                        ):

                            try:

                                modelos = json.loads(
                                    modelos
                                )

                            except json.JSONDecodeError:

                                modelos = [
                                    modelos
                                ]

                        modelos_json = json.dumps(
                            modelos,
                            ensure_ascii=False
                        )

                except (
                    TypeError,
                    ValueError
                ):

                    modelos_json = None

            # ------------------------------------------------
            # Convertir valores NaN
            # ------------------------------------------------

            valores = [
                fila["lead_id"],
                fila["modelo_conversacion"],
                modelos_json,
                fila["presupuesto"],
                fila["cuota_inicial"],
                fila["forma_pago"],
                fila["intencion_compra"],
                fila["objecion_principal"],
                convertir_booleano(
                    fila["solicita_cotizacion"]
                ),
                convertir_booleano(
                    fila["solicita_visita"]
                ),
                fila["resumen_conversacion"],
                fila["confianza_extraccion"],
            ]

            valores_limpios = []

            for valor in valores:

                try:

                    if pd.isna(valor):
                        valor = None

                except (
                    TypeError,
                    ValueError
                ):

                    pass

                valores_limpios.append(
                    valor
                )

            registros.append(
                tuple(valores_limpios)
            )

        conexion = obtener_conexion()

        with conexion.cursor() as cursor:

            cursor.executemany(
                sql,
                registros
            )

        conexion.commit()

        conexion.close()

        return

    # ========================================================
    # SQLITE
    # ========================================================

    datos[
        "modelos_alternativos"
    ] = datos[
        "modelos_alternativos"
    ].apply(
        lambda x: (
            json.dumps(
                x,
                ensure_ascii=False
            )
            if isinstance(x, list)
            else x
        )
    )

    conexion = obtener_conexion()

    cursor = conexion.cursor()

    lead_ids = datos[
        "lead_id"
    ].tolist()

    if lead_ids:

        placeholders = ",".join(
            ["?"] * len(lead_ids)
        )

        cursor.execute(
            f"""
            DELETE FROM extracciones_ia
            WHERE lead_id IN ({placeholders})
            """,
            lead_ids
        )

    sql = """
        INSERT INTO extracciones_ia (
            lead_id,
            modelo_conversacion,
            modelos_alternativos,
            presupuesto,
            cuota_inicial,
            forma_pago,
            intencion_compra,
            objecion_principal,
            solicita_cotizacion,
            solicita_visita,
            resumen_conversacion,
            confianza_extraccion
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """

    registros = [
        tuple(fila)
        for fila in datos.itertuples(
            index=False,
            name=None
        )
    ]

    cursor.executemany(
        sql,
        registros
    )

    conexion.commit()

    conexion.close()


# ============================================================
# CARGAR EXTRACCIONES IA
# ============================================================

def cargar_extracciones_ia():

    conexion = obtener_conexion()

    consulta = """
        SELECT
            lead_id,
            modelo_conversacion,
            modelos_alternativos,
            presupuesto,
            cuota_inicial,
            forma_pago,
            intencion_compra,
            objecion_principal,
            solicita_cotizacion,
            solicita_visita,
            resumen_conversacion,
            confianza_extraccion
        FROM extracciones_ia
    """

    datos = pd.read_sql_query(
        consulta,
        conexion
    )

    conexion.close()

    return datos


# ============================================================
# PRUEBA
# ============================================================

if __name__ == "__main__":

    crear_tablas()

    if usa_postgresql():

        print(
            "Base de datos PostgreSQL/Supabase configurada."
        )

    else:

        print(
            "Base de datos SQLite local configurada."
        )