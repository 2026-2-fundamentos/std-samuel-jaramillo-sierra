import shutil
import string
import time
from pathlib import Path

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ACTIVITY_DIR / "data"
INPUT_DIR = ACTIVITY_DIR / "temp" / "input"
OUTPUT_DIR = ACTIVITY_DIR / "temp" / "output"
SUBMISSION_DIR = ACTIVITY_DIR / "submission"

N_COPIES = 1000


def reset_directory(directory):
    """La carpeta debe existir y estar vacia."""
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)


def generate_input_files():
    """Genera N_COPIES copias de cada archivo de data/ en temp/input/."""
    reset_directory(INPUT_DIR)
    for file in DATA_DIR.glob("*.txt"):
        text = file.read_text(encoding="utf-8")
        for i in range(1, N_COPIES + 1):
            new_file = INPUT_DIR / f"{file.stem}_{i:05d}.txt"
            new_file.write_text(text, encoding="utf-8")


def read_input_files():
    """Lee los archivos de temp/input/ como una secuencia de (archivo, linea)."""
    sequence = []
    for file in INPUT_DIR.glob("*.txt"):
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                sequence.append((file.name, line))
    return sequence


def mapper(sequence):
    """Emite el par (palabra, 1) por cada palabra de cada linea."""
    translation = str.maketrans("", "", string.punctuation)
    pairs_sequence = []
    for _, line in sequence:
        line = line.lower().translate(translation)
        for word in line.split():
            pairs_sequence.append((word, 1))
    return pairs_sequence


def shuffle_and_sort(pairs_sequence):
    """Ordena los pares para que las claves iguales queden contiguas."""
    return sorted(pairs_sequence)


def reducer(pairs_sequence):
    """Suma los valores de cada clave (los pares deben venir ordenados)."""
    result = []
    for key, value in pairs_sequence:
        if result and result[-1][0] == key:
            result[-1] = (key, result[-1][1] + value)
        else:
            result.append((key, value))
    return result


def write_output(result):
    """Escribe el conteo en part-00000 y el marcador _SUCCESS."""
    reset_directory(OUTPUT_DIR)
    with open(OUTPUT_DIR / "part-00000", "w", encoding="utf-8") as f:
        for key, value in result:
            f.write(f"{key}\t{value}\n")
    (OUTPUT_DIR / "_SUCCESS").write_text("", encoding="utf-8")


def copy_to_submission():
    """Copia el resultado desde el HDFS simulado al disco local."""
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    for file in OUTPUT_DIR.iterdir():
        shutil.copy2(file, SUBMISSION_DIR)


def main():
    generate_input_files()

    start_time = time.time()

    sequence = read_input_files()
    pairs_sequence = mapper(sequence)
    pairs_sequence = shuffle_and_sort(pairs_sequence)
    result = reducer(pairs_sequence)
    write_output(result)
    copy_to_submission()

    end_time = time.time()
    print(f"Tiempo de ejecución: {end_time - start_time:.2f} segundos")


if __name__ == "__main__":
    main()
