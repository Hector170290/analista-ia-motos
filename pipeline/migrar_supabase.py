import json
import os
import sqlite3
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_PATH = BASE_DIR / "data" / "motos.db"

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "No se encontró DATABASE_URL en el archivo .env"
    )


def convertir_none(valor):

    if valor is None:
        return None

    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass

    return valor


def convertir_booleano(valor):

    if valor is None:
        return None

    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass

    return bool(valor)


def convertir_fecha(valor):

    if valor is None:
        return None

    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(valor, "to_pydatetime"):
        return valor.to_pydatetime()

    return valor


def convertir_modelos_alternativos(valor):
    """
    Convierte cualquier formato de modelos_alternativos
    en una lista JSON válida para PostgreSQL.
    """

    if valor is None:
        return None

    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass

    # Si ya es una lista
    if isinstance(valor, list):

        return valor

    # Si ya es un diccionario
    if isinstance(valor, dict):

        return [valor]

    texto = str(valor).strip()

    if not texto:
        return None

    # --------------------------------------------------------
    # Intentar leer JSON válido
    # --------------------------------------------------------

    try:

        resultado = json.loads(texto)

        if resultado is None:
            return None

        if isinstance(resultado, list):
            return resultado

        return [resultado]

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Caso:
    #
    # {"Suzuki Gixxer 150"}
    #
    # Esto NO es JSON válido.
    # Lo convertimos a:
    #
    # ["Suzuki Gixxer 150"]
    # --------------------------------------------------------

    if texto.startswith("{") and texto.endswith("}"):

        contenido = texto[1:-1].strip()

        if not contenido:
            return []

        elementos = [
            elemento.strip().strip('"').strip("'")
            for elemento in contenido.split(",")
        ]

        elementos = [
            elemento
            for elemento in elementos
            if elemento
        ]

        return elementos

    # --------------------------------------------------------
    # Cualquier otro texto
    # --------------------------------------------------------

    return [texto]


# ============================================================
# CARGAR SQLITE
# ============================================================

def cargar_sqlite():

    if not SQLITE_PATH.exists():

        raise FileNotFoundError(
            f"No se encontró la base SQLite: {SQLITE_PATH}"
        )

    conexion = sqlite3.connect(
        SQLITE_PATH
    )

    leads = pd.read_sql_query(
        "SELECT * FROM leads",
        conexion
    )

    extracciones = pd.read_sql_query(
        "SELECT * FROM extracciones_ia",
        conexion
    )

    conexion.close()

    return leads, extracciones


# ============================================================
# ASESORES
# ============================================================

def migrar_asesores(conexion):

    ruta = BASE_DIR / "asesores.csv"

    asesores = pd.read_csv(
        ruta,
        encoding="utf-8-sig"
    )

    sql = """
        INSERT INTO asesores (
            asesor_id,
            nombre,
            punto_venta_id,
            empresa_id,
            capacidad_diaria_leads,
            activo,
            fecha_ingreso
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (asesor_id)
        DO UPDATE SET
            nombre = EXCLUDED.nombre,
            punto_venta_id = EXCLUDED.punto_venta_id,
            empresa_id = EXCLUDED.empresa_id,
            capacidad_diaria_leads = EXCLUDED.capacidad_diaria_leads,
            activo = EXCLUDED.activo,
            fecha_ingreso = EXCLUDED.fecha_ingreso
    """

    registros = []

    for _, fila in asesores.iterrows():

        fecha_ingreso = pd.to_datetime(
            fila["fecha_ingreso"],
            errors="coerce"
        )

        registros.append(
            (
                convertir_none(fila["asesor_id"]),
                convertir_none(fila["nombre"]),
                convertir_none(fila["punto_venta_id"]),
                convertir_none(fila["empresa_id"]),
                convertir_none(
                    fila["capacidad_diaria_leads"]
                ),
                convertir_none(fila["activo"]),
                convertir_fecha(fecha_ingreso),
            )
        )

    with conexion.cursor() as cursor:

        cursor.executemany(
            sql,
            registros
        )

    print(
        f"Asesores migrados: {len(registros)}"
    )


# ============================================================
# CLIENTES
# ============================================================

def migrar_clientes(
    conexion,
    leads
):

    clientes = (
        leads[
            [
                "cliente_id",
                "nombre_cliente",
                "telefono",
                "email",
                "ciudad",
            ]
        ]
        .drop_duplicates(
            subset="cliente_id"
        )
        .copy()
    )

    sql = """
        INSERT INTO clientes (
            cliente_id,
            nombre_cliente,
            telefono,
            email,
            ciudad
        )
        VALUES (
            %s, %s, %s, %s, %s
        )
        ON CONFLICT (cliente_id)
        DO UPDATE SET
            nombre_cliente = EXCLUDED.nombre_cliente,
            telefono = EXCLUDED.telefono,
            email = EXCLUDED.email,
            ciudad = EXCLUDED.ciudad
    """

    registros = []

    for _, fila in clientes.iterrows():

        registros.append(
            (
                convertir_none(fila["cliente_id"]),
                convertir_none(fila["nombre_cliente"]),
                convertir_none(fila["telefono"]),
                convertir_none(fila["email"]),
                convertir_none(fila["ciudad"]),
            )
        )

    with conexion.cursor() as cursor:

        cursor.executemany(
            sql,
            registros
        )

    print(
        f"Clientes migrados: {len(registros)}"
    )


# ============================================================
# OPORTUNIDADES
# ============================================================

def migrar_oportunidades(
    conexion,
    leads
):

    oportunidades = (
        leads[
            [
                "oportunidad_id",
                "cliente_id",
                "modelo_homologado",
                "estado_oportunidad",
            ]
        ]
        .dropna(
            subset=["oportunidad_id"]
        )
        .drop_duplicates(
            subset="oportunidad_id"
        )
        .copy()
    )

    sql = """
        INSERT INTO oportunidades (
            oportunidad_id,
            cliente_id,
            modelo_homologado,
            estado_oportunidad
        )
        VALUES (
            %s, %s, %s, %s
        )
        ON CONFLICT (oportunidad_id)
        DO UPDATE SET
            cliente_id = EXCLUDED.cliente_id,
            modelo_homologado = EXCLUDED.modelo_homologado,
            estado_oportunidad = EXCLUDED.estado_oportunidad
    """

    registros = []

    for _, fila in oportunidades.iterrows():

        registros.append(
            (
                convertir_none(
                    fila["oportunidad_id"]
                ),
                convertir_none(
                    fila["cliente_id"]
                ),
                convertir_none(
                    fila["modelo_homologado"]
                ),
                convertir_none(
                    fila["estado_oportunidad"]
                ),
            )
        )

    with conexion.cursor() as cursor:

        cursor.executemany(
            sql,
            registros
        )

    print(
        f"Oportunidades migradas: {len(registros)}"
    )


# ============================================================
# LEADS
# ============================================================

def migrar_leads(
    conexion,
    leads
):

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
        "prioridad",
        "asesor_id",
        "asesor_nombre",
        "estado_asignacion",
    ]

    datos = leads.copy()

    for columna in columnas:

        if columna not in datos.columns:
            datos[columna] = None

    datos = datos[columnas]

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
            prioridad,
            asesor_id,
            asesor_nombre,
            estado_asignacion
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
            fecha_registro_normalizada = EXCLUDED.fecha_registro_normalizada,
            fecha_primer_contacto = EXCLUDED.fecha_primer_contacto,
            canal = EXCLUDED.canal,
            empresa_id = EXCLUDED.empresa_id,
            punto_venta_id = EXCLUDED.punto_venta_id,
            nombre_cliente = EXCLUDED.nombre_cliente,
            telefono = EXCLUDED.telefono,
            email = EXCLUDED.email,
            ciudad = EXCLUDED.ciudad,
            modelo_interes_texto = EXCLUDED.modelo_interes_texto,
            modelo_homologado = EXCLUDED.modelo_homologado,
            estado_modelo = EXCLUDED.estado_modelo,
            estado_oportunidad = EXCLUDED.estado_oportunidad,
            tiene_conversacion = EXCLUDED.tiene_conversacion,
            prioridad = EXCLUDED.prioridad,
            asesor_id = EXCLUDED.asesor_id,
            asesor_nombre = EXCLUDED.asesor_nombre,
            estado_asignacion = EXCLUDED.estado_asignacion
    """

    registros = []

    for _, fila in datos.iterrows():

        fecha_normalizada = pd.to_datetime(
            fila["fecha_registro_normalizada"],
            errors="coerce"
        )

        registros.append(
            (
                convertir_none(
                    fila["lead_id"]
                ),
                convertir_none(
                    fila["cliente_id"]
                ),
                convertir_none(
                    fila["oportunidad_id"]
                ),
                convertir_none(
                    fila["fecha_registro"]
                ),
                convertir_fecha(
                    fecha_normalizada
                ),
                convertir_none(
                    fila["fecha_primer_contacto"]
                ),
                convertir_none(
                    fila["canal"]
                ),
                convertir_none(
                    fila["empresa_id"]
                ),
                convertir_none(
                    fila["punto_venta_id"]
                ),
                convertir_none(
                    fila["nombre_cliente"]
                ),
                convertir_none(
                    fila["telefono"]
                ),
                convertir_none(
                    fila["email"]
                ),
                convertir_none(
                    fila["ciudad"]
                ),
                convertir_none(
                    fila["modelo_interes_texto"]
                ),
                convertir_none(
                    fila["modelo_homologado"]
                ),
                convertir_none(
                    fila["estado_modelo"]
                ),
                convertir_none(
                    fila["estado_oportunidad"]
                ),
                convertir_booleano(
                    fila["tiene_conversacion"]
                ),
                convertir_none(
                    fila["prioridad"]
                ),
                convertir_none(
                    fila["asesor_id"]
                ),
                convertir_none(
                    fila["asesor_nombre"]
                ),
                convertir_none(
                    fila["estado_asignacion"]
                ),
            )
        )

    with conexion.cursor() as cursor:

        cursor.executemany(
            sql,
            registros
        )

    print(
        f"Leads migrados: {len(registros)}"
    )


# ============================================================
# EXTRACCIONES IA
# ============================================================

def migrar_extracciones_ia(
    conexion,
    extracciones
):

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

    datos = extracciones.copy()

    for columna in columnas:

        if columna not in datos.columns:
            datos[columna] = None

    datos = datos[columnas]

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
            modelo_conversacion = EXCLUDED.modelo_conversacion,
            modelos_alternativos = EXCLUDED.modelos_alternativos,
            presupuesto = EXCLUDED.presupuesto,
            cuota_inicial = EXCLUDED.cuota_inicial,
            forma_pago = EXCLUDED.forma_pago,
            intencion_compra = EXCLUDED.intencion_compra,
            objecion_principal = EXCLUDED.objecion_principal,
            solicita_cotizacion = EXCLUDED.solicita_cotizacion,
            solicita_visita = EXCLUDED.solicita_visita,
            resumen_conversacion = EXCLUDED.resumen_conversacion,
            confianza_extraccion = EXCLUDED.confianza_extraccion
    """

    registros = []

    for _, fila in datos.iterrows():

        modelos_alternativos = (
            convertir_modelos_alternativos(
                fila["modelos_alternativos"]
            )
        )

        # Convertimos la lista/diccionario a JSON real.
        # Esto garantiza que PostgreSQL reciba un JSON válido.
        if modelos_alternativos is not None:

            modelos_alternativos = json.dumps(
                modelos_alternativos,
                ensure_ascii=False
            )

        registros.append(
            (
                convertir_none(
                    fila["lead_id"]
                ),

                convertir_none(
                    fila["modelo_conversacion"]
                ),

                modelos_alternativos,

                convertir_none(
                    fila["presupuesto"]
                ),

                convertir_none(
                    fila["cuota_inicial"]
                ),

                convertir_none(
                    fila["forma_pago"]
                ),

                convertir_none(
                    fila["intencion_compra"]
                ),

                convertir_none(
                    fila["objecion_principal"]
                ),

                convertir_booleano(
                    fila["solicita_cotizacion"]
                ),

                convertir_booleano(
                    fila["solicita_visita"]
                ),

                convertir_none(
                    fila["resumen_conversacion"]
                ),

                convertir_none(
                    fila["confianza_extraccion"]
                ),
            )
        )

    with conexion.cursor() as cursor:

        cursor.executemany(
            sql,
            registros
        )

    print(
        f"Extracciones IA migradas: {len(registros)}"
    )


# ============================================================
# VALIDACIÓN
# ============================================================

def validar_migracion(conexion):

    consultas = {

        "clientes":
            "SELECT COUNT(*) FROM clientes",

        "oportunidades":
            "SELECT COUNT(*) FROM oportunidades",

        "asesores":
            "SELECT COUNT(*) FROM asesores",

        "leads":
            "SELECT COUNT(*) FROM leads",

        "extracciones_ia":
            "SELECT COUNT(*) FROM extracciones_ia",
    }

    print()
    print("=" * 50)
    print("VALIDACIÓN DE MIGRACIÓN")
    print("=" * 50)

    with conexion.cursor() as cursor:

        for nombre, consulta in consultas.items():

            cursor.execute(
                consulta
            )

            cantidad = cursor.fetchone()[0]

            print(
                f"{nombre}: {cantidad}"
            )

    print("=" * 50)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 50)
    print("MIGRACIÓN SQLITE → SUPABASE")
    print("=" * 50)
    print()

    print(
        f"Leyendo SQLite: {SQLITE_PATH}"
    )

    leads, extracciones = cargar_sqlite()

    print(
        f"Leads encontrados: {len(leads)}"
    )

    print(
        f"Extracciones IA encontradas: {len(extracciones)}"
    )

    print()
    print(
        "Conectando con Supabase..."
    )

    with psycopg.connect(
        DATABASE_URL,
        sslmode="require"
    ) as conexion:

        migrar_asesores(
            conexion
        )

        migrar_clientes(
            conexion,
            leads
        )

        migrar_oportunidades(
            conexion,
            leads
        )

        migrar_leads(
            conexion,
            leads
        )

        migrar_extracciones_ia(
            conexion,
            extracciones
        )

        conexion.commit()

        validar_migracion(
            conexion
        )

    print()
    print(
        "MIGRACIÓN FINALIZADA CORRECTAMENTE"
    )
    print()


if __name__ == "__main__":

    main()