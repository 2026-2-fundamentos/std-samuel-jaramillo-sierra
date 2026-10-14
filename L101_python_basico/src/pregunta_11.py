import csv
import gzip
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "data.csv.gz"


def pregunta_11():
    """
    La cuarta columna (`codes`) contiene letras minúsculas separadas por
    comas. Para cada una de esas letras, sume los valores de la segunda
    columna (`value`) de los registros en los que aparece. Retorne un
    diccionario `{letra: suma}` con las letras en orden alfabético.

    Ejemplo del formato de la respuesta:

        {"a": 122, "b": 49, "c": 91, ...}
    """

    with gzip.open(DATA_FILE, "rt", encoding="utf-8") as file:
        rows = list(csv.reader(file, delimiter="\t"))

    sums = {}
    for row in rows:
        value = int(row[1])
        for code in row[3].split(","):
            sums[code] = sums.get(code, 0) + value

    return dict(sorted(sums.items()))
