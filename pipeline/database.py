import json
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "motos.db"


def obtener_conexion():
    """
    Crea y devuelve una conexión a la base de datos SQLite.
    """

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    conexion = sqlite3.connect(DB_PATH)

    return conexion


def crear_tablas():
    """
    Crea las tablas principales del sistema.
    """

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            lead_id TEXT PRIMARY KEY,
            cliente_id TEXT,
            oportunidad_id TEXT,
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
            tiene_conversacion INTEGER
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
    Guarda los leads procesados en la tabla leads.
    """

    conexion = obtener_conexion()

    columnas = [
        "lead_id",
        "cliente_id",
        "oportunidad_id",
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
    ]

    datos = df.copy()

    for columna in columnas:
        if columna not in datos.columns:
            datos[columna] = None

    datos = datos[columnas]

    datos.to_sql(
        "leads",
        conexion,
        if_exists="replace",
        index=False
    )

    conexion.close()


def guardar_extracciones_ia(df):
    """
    Guarda las extracciones realizadas por IA.

    Si el lead ya existe, actualiza su información.
    Si no existe, crea un nuevo registro.
    """

    conexion = obtener_conexion()

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

    # Solo guardar registros realmente procesados por IA
    datos = datos[
        datos["confianza_extraccion"].notna()
    ].copy()

    if datos.empty:
        conexion.close()
        return

    for columna in columnas:
        if columna not in datos.columns:
            datos[columna] = None

    datos = datos[columnas]

    # Convertir listas a JSON para SQLite
    datos["modelos_alternativos"] = datos[
        "modelos_alternativos"
    ].apply(
        lambda x: json.dumps(
            x,
            ensure_ascii=False
        )
        if isinstance(x, list)
        else x
    )

    cursor = conexion.cursor()

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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(lead_id)
        DO UPDATE SET
            modelo_conversacion = excluded.modelo_conversacion,
            modelos_alternativos = excluded.modelos_alternativos,
            presupuesto = excluded.presupuesto,
            cuota_inicial = excluded.cuota_inicial,
            forma_pago = excluded.forma_pago,
            intencion_compra = excluded.intencion_compra,
            objecion_principal = excluded.objecion_principal,
            solicita_cotizacion = excluded.solicita_cotizacion,
            solicita_visita = excluded.solicita_visita,
            resumen_conversacion = excluded.resumen_conversacion,
            confianza_extraccion = excluded.confianza_extraccion
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


if __name__ == "__main__":

    crear_tablas()

    print("Base de datos creada correctamente")
    print(f"Ubicación: {DB_PATH}")