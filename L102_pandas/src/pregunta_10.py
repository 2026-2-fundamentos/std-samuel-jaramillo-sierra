import pandas as pd


def pregunta_10():
    """
    Usando `data/tbl0.tsv`, construya para cada categoría de la columna `c1`
    un texto con todos sus valores de la columna `c2`, ordenados de menor a
    mayor y separados por `:`. Retorne un DataFrame cuyo índice son las
    categorías, en orden alfabético, con una única columna llamada `c2`.

    Ejemplo del formato de la respuesta:

                           c2
        c1
        A     1:1:2:3:6:7:8:9
        B       1:3:4:5:6:8:9
        C           0:5:6:7:9
        ...
    """

    df = pd.read_csv("data/tbl0.tsv", sep="\t")

    categorias = sorted(df["c1"].unique())

    textos = []
    for categoria in categorias:
        valores = df[df["c1"] == categoria]["c2"]
        valores = sorted(valores)

        partes = []
        for valor in valores:
            partes.append(str(valor))

        textos.append(":".join(partes))

    resultado = pd.DataFrame({"c2": textos}, index=categorias)
    resultado.index.name = "c1"

    return resultado
