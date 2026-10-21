import os

import pandas as pd


def pregunta_01():
    """
    Las frases de este laboratorio no están en una tabla, sino en miles de
    archivos de texto organizados en carpetas. Dentro de `data/` hay dos
    carpetas, `train/` y `test/`, y cada una contiene las carpetas
    `negative/`, `neutral/` y `positive/`. Cada archivo `.txt` contiene una
    frase, y la carpeta donde se encuentra indica su sentimiento.

    Su tarea es construir un dataset para cada división y guardarlo en:

    - `submission/train_dataset.csv`
    - `submission/test_dataset.csv`

    Cada archivo debe tener dos columnas: `phrase`, con el texto de la frase,
    y `target`, con el nombre de la carpeta de sentimiento (`negative`,
    `neutral` o `positive`). Recorra las carpetas y los archivos en orden
    alfabético, de modo que el resultado sea siempre el mismo. No guarde el
    índice de Pandas en el CSV.

    Ejemplo del formato de cada archivo:

        phrase,target
        "The real estate company posted a net loss ...",negative
        ...
        "Cardona slowed her vehicle , turned around ...",neutral
        ...
    """

    os.makedirs("submission", exist_ok=True)

    for division in ["train", "test"]:
        frases = []
        sentimientos = []

        carpeta_division = os.path.join("data", division)

        # Cada subcarpeta (negative, neutral, positive) es un sentimiento
        for sentimiento in sorted(os.listdir(carpeta_division)):
            carpeta_sentimiento = os.path.join(carpeta_division, sentimiento)

            # Se ignoran archivos sueltos, como el .DS_Store de macOS
            if not os.path.isdir(carpeta_sentimiento):
                continue

            for nombre_archivo in sorted(os.listdir(carpeta_sentimiento)):
                if not nombre_archivo.endswith(".txt"):
                    continue

                ruta = os.path.join(carpeta_sentimiento, nombre_archivo)
                with open(ruta, "r", encoding="utf-8") as archivo:
                    # strip() quita los espacios sobrantes al inicio y al final
                    frases.append(archivo.read().strip())
                sentimientos.append(sentimiento)

        df = pd.DataFrame({"phrase": frases, "target": sentimientos})
        df.to_csv(f"submission/{division}_dataset.csv", index=False)
