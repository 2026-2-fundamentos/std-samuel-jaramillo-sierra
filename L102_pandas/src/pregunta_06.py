import pandas as pd


def pregunta_06():
    """
    Usando `data/tbl1.tsv`, obtenga los valores distintos de la columna `c4`,
    conviértalos a mayúsculas y retórnelos como una lista ordenada
    alfabéticamente.

    Ejemplo del formato de la respuesta:

        ["A", "B", "C", "D", "E", "F", "G"]
    """

    df = pd.read_csv("data/tbl1.tsv", sep="\t")

    letras = df["c4"].unique()

    resultado = []
    for letra in letras:
        resultado.append(letra.upper())

    resultado.sort()

    return resultado
