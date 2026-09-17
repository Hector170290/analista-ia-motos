import pandas as pd


class UnionFind:
    def __init__(self, elementos):
        self.padre = {elemento: elemento for elemento in elementos}

    def encontrar(self, elemento):
        if self.padre[elemento] != elemento:
            self.padre[elemento] = self.encontrar(
                self.padre[elemento]
            )
        return self.padre[elemento]

    def unir(self, elemento_a, elemento_b):
        raiz_a = self.encontrar(elemento_a)
        raiz_b = self.encontrar(elemento_b)

        if raiz_a != raiz_b:
            self.padre[raiz_b] = raiz_a


def identificar_clientes(df):
    df = df.copy()

    columnas = [
        "telefono_normalizado",
        "nombre_cliente_normalizado",
        "email_normalizado",
    ]

    for columna in columnas:
        if columna not in df.columns:
            df[columna] = None

    leads = list(df.index)

    uf = UnionFind(leads)

    identificadores = {}

    for indice, fila in df.iterrows():

        valores = [
            ("telefono", fila["telefono_normalizado"]),
            ("nombre", fila["nombre_cliente_normalizado"]),
            ("email", fila["email_normalizado"]),
        ]

        for tipo, valor in valores:

            if pd.isna(valor):
                continue

            valor = str(valor).strip()

            if not valor:
                continue

            clave = (tipo, valor)

            if clave in identificadores:
                uf.unir(
                    indice,
                    identificadores[clave]
                )
            else:
                identificadores[clave] = indice

    grupos = {}

    for indice in leads:

        raiz = uf.encontrar(indice)

        if raiz not in grupos:
            grupos[raiz] = f"CLI-{len(grupos) + 1:05d}"

    df["cliente_id"] = [
        grupos[uf.encontrar(indice)]
        for indice in df.index
    ]

    return df


def eliminar_duplicados_lead(df):
    """
    Elimina registros duplicados utilizando lead_id.

    Conserva la primera aparición de cada lead_id.
    No elimina registros por teléfono, nombre o email.
    """

    df = df.copy()

    if "lead_id" not in df.columns:
        raise ValueError(
            "El DataFrame no contiene la columna 'lead_id'."
        )

    df = df.drop_duplicates(
        subset="lead_id",
        keep="first"
    ).reset_index(drop=True)

    return df


