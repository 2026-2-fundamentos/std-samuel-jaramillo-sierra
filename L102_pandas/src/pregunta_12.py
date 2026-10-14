import pandas as pd


def pregunta_12():
    """
    En `data/tbl2.tsv`, cada valor de la columna `c0` aparece en varias
    filas. Construya un DataFrame con una fila por cada valor de `c0`, en
    orden ascendente, y las columnas `c0` y `c5`. En `c5`, forme un texto
    `c5a:c5b` para cada fila de ese `c0`, ordene esos textos alfabéticamente y
    únalos separados por comas.

    Ejemplo del formato de la respuesta:

            c0                             c5
        0    0  bbb:0,ddd:9,ggg:8,hhh:2,jjj:3
        1    1        aaa:3,ccc:2,ddd:0,hhh:9
        2    2        ccc:6,ddd:2,ggg:5,jjj:1
        ...
    """

    df = pd.read_csv("data/tbl2.tsv", sep="\t")

    # Une las dos columnas en un solo texto: "jjj" y 3 -> "jjj:3"
    df["c5"] = df["c5a"] + ":" + df["c5b"].astype(str)

    valores_c0 = sorted(df["c0"].unique())

    textos = []
    for valor in valores_c0:
        pares = df[df["c0"] == valor]["c5"]
        pares = sorted(pares)
        textos.append(",".join(pares))

    resultado = pd.DataFrame({"c0": valores_c0, "c5": textos})

    return resultado
