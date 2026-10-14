import pandas as pd


def pregunta_01():
    """
    El archivo `data/clusters_report.txt` es un reporte de clústeres de
    palabras clave pensado para ser leído por una persona, no por un programa:
    los encabezados ocupan varias líneas, las columnas están alineadas con
    espacios y la lista de palabras clave de un clúster continúa en las líneas
    siguientes.

    Su tarea es convertir ese reporte en un DataFrame de Pandas con una fila
    por clúster y las columnas:

    - `cluster`: número del clúster, como entero.
    - `cantidad_de_palabras_clave`: como entero.
    - `porcentaje_de_palabras_clave`: como número decimal; por ejemplo, el
      texto `15,9 %` debe quedar como `15.9`.
    - `principales_palabras_clave`: todas las palabras clave del clúster en un
      solo texto, separadas por una coma y un único espacio.

    Retorne el DataFrame.

    Ejemplo del formato de la respuesta (se omite la última columna):

           cluster  cantidad_de_palabras_clave  porcentaje_de_palabras_clave
        0        1                         105                          15.9
        1        2                         102                          15.4
        ...
    """

    with open("data/clusters_report.txt", "r", encoding="utf-8") as archivo:
        lineas = archivo.readlines()

    # Las primeras 4 líneas son el encabezado del reporte
    lineas = lineas[4:]

    clusters = []
    cantidades = []
    porcentajes = []
    palabras = []

    for linea in lineas:
        partes = linea.split()

        # Línea vacía: separa un clúster del siguiente
        if len(partes) == 0:
            continue

        # Si la línea empieza con un número, es el inicio de un clúster nuevo
        if partes[0].isdigit():
            clusters.append(int(partes[0]))
            cantidades.append(int(partes[1]))
            porcentajes.append(float(partes[2].replace(",", ".")))
            # partes[3] es el símbolo "%"; desde partes[4] son palabras clave
            palabras.append(" ".join(partes[4:]))

        # Si no, son más palabras clave del clúster anterior
        else:
            palabras[-1] = palabras[-1] + " " + " ".join(partes)

    # Limpieza: sin punto final y cada palabra clave separada por ", "
    textos_limpios = []
    for texto in palabras:
        if texto.endswith("."):
            texto = texto[:-1]

        lista_limpia = []
        for palabra in texto.split(","):
            lista_limpia.append(palabra.strip())

        textos_limpios.append(", ".join(lista_limpia))

    df = pd.DataFrame(
        {
            "cluster": clusters,
            "cantidad_de_palabras_clave": cantidades,
            "porcentaje_de_palabras_clave": porcentajes,
            "principales_palabras_clave": textos_limpios,
        }
    )

    return df
