import pandas as pd


def asignar_oportunidades(df):
    """
    Asigna una oportunidad comercial a cada lead
    cuando existe un modelo homologado.

    Regla:
    - mismo cliente + mismo modelo = misma oportunidad
    - mismo cliente + modelo diferente = oportunidad diferente
    - sin modelo homologado = pendiente de información
    """

    df = df.copy()

    df["oportunidad_id"] = None

    # Solo podemos identificar una oportunidad
    # cuando conocemos el modelo de la moto.
    mask_modelo = (
        df["cliente_id"].notna()
        & df["modelo_homologado"].notna()
    )

    claves = (
        df.loc[mask_modelo, "cliente_id"].astype(str)
        + "_"
        + df.loc[mask_modelo, "modelo_homologado"].astype(str)
    )

    mapa_oportunidades = {
        clave: f"OP-{i:05d}"
        for i, clave in enumerate(
            claves.unique(),
            start=1
        )
    }

    df.loc[mask_modelo, "oportunidad_id"] = (
        claves.map(mapa_oportunidades)
    )

    # Estado de la oportunidad
    df["estado_oportunidad"] = "PENDIENTE_MODELO"

    df.loc[
        df["oportunidad_id"].notna(),
        "estado_oportunidad"
    ] = "IDENTIFICADA"

    return df