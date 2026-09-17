import json
import sqlite3
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "motos.db"


def obtener_conexion():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conexion = sqlite3.connect(DB_PATH)

    return conexion


def crear_tablas():
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


def guardar_leads(df):
    """
    Guarda los leads en SQLite.

    Se utiliza DELETE + INSERT para conservar
    la estructura y restricciones de la tabla.
    """

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

    # Convertir fechas datetime a texto
    # para almacenarlas correctamente en SQLite.
    for columna in [
        "fecha_registro_normalizada"
    ]:

        if columna in datos.columns:

            datos[columna] = datos[columna].apply(
                lambda x: (
                    x.isoformat()
                    if hasattr(x, "isoformat")
                    else x
                )
            )

    conexion = obtener_conexion()

    cursor = conexion.cursor()

    # Reemplazar los registros existentes
    # sin destruir la estructura de la tabla.
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


def guardar_extracciones_ia(df):
    """
    Guarda las extracciones realizadas por IA.
    """

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

    datos["modelos_alternativos"] = (
        datos["modelos_alternativos"].apply(
            lambda x: (
                json.dumps(
                    x,
                    ensure_ascii=False
                )
                if isinstance(x, list)
                else x
            )
        )
    )

    conexion = obtener_conexion()

    cursor = conexion.cursor()

    lead_ids = datos["lead_id"].tolist()

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


def cargar_extracciones_ia():
    """
    Recupera las extracciones almacenadas.
    """

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


if __name__ == "__main__":

    crear_tablas()

    print(
        "Base de datos creada correctamente"
    )

    print(
        f"Ubicación: {DB_PATH}"
    )