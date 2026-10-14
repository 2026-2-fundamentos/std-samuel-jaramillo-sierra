import csv
import gzip
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "data.csv.gz"


def pregunta_06():
    """
    La quinta columna (`metrics`) contiene pares `clave:valor` separados por
    comas. Para cada clave, encuentre el valor mínimo y el valor máximo que
    aparecen en todo el archivo. Retorne una lista de tuplas
    `(clave, mínimo, máximo)` ordenada alfabéticamente por la clave.

    Observe que el orden es mínimo y luego máximo, al contrario de la
    pregunta 5.

    Ejemplo del formato de la respuesta:

        [("aaa", 1, 9), ("bbb", 1, 9), ...]
    """

    with gzip.open(DATA_FILE, "rt", encoding="utf-8") as file:
        rows = list(csv.reader(file, delimiter="\t"))

    values = {}
    for row in rows:
        for pair in row[4].split(","):
            key, value = pair.split(":")  # "jjj:12" -> "jjj", "12"
            values.setdefault(key, []).append(int(value))

    return [
        (key, min(key_values), max(key_values))
        for key, key_values in sorted(values.items())
    ]
