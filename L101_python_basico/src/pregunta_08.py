import csv
import gzip
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "data.csv.gz"


def pregunta_08():
    """
    Repita la pregunta 7, pero ahora cada lista de letras debe contener cada
    letra una sola vez y estar ordenada alfabéticamente. Retorne una lista de
    tuplas `(valor, letras)` ordenada por el valor.

    Ejemplo del formato de la respuesta:

        [(0, ["C"]), (1, ["B", "E"]), (2, ["A", "E"]), ...]
    """

    with gzip.open(DATA_FILE, "rt", encoding="utf-8") as file:
        rows = list(csv.reader(file, delimiter="\t"))

    letters = {}
    for row in rows:
        letters.setdefault(int(row[1]), []).append(row[0])

    return [
        (value, sorted(set(value_letters)))
        for value, value_letters in sorted(letters.items())
    ]
