import json
import os
import re

import pandas as pd


def main():
    """
    Antes de limpiar o analizar un conjunto de datos, un analista debe
    documentar qué problemas tiene. En este laboratorio usted no va a limpiar
    `data/ventas.csv.gz`: va a construir un reporte de calidad que deje evidencia
    de sus problemas, tal como están en el archivo.

    Lea `data/ventas.csv.gz` sin modificar sus valores. Para trabajar con los
    encabezados, normalícelos: páselos a minúsculas, elimine los espacios al
    inicio y al final (y cualquier marca BOM) y reemplace los espacios
    internos por `_`. Las columnas requeridas son `supplier_id`, `supplier`,
    `country`, `city`, `purchase_date`, `amount`, `discount`, `weight`,
    `units`, `unit_price` y `contact_email`.

    Escriba el reporte en `submission/data_quality_report.json` con estas
    claves:

    - `row_count`: cantidad de filas de datos.
    - `column_count`: cantidad de columnas.
    - `missing_required_columns`: lista ordenada de columnas requeridas que no
      están en el archivo.
    - `unexpected_columns`: lista ordenada de columnas del archivo que no son
      requeridas.
    - `duplicate_row_count`: cantidad de filas idénticas a una fila anterior.
    - `duplicate_supplier_id_row_count`: cantidad de filas cuyo `supplier_id`
      aparece más de una vez (cuente todas esas filas, no solo las
      repetidas).
    - `missing_value_count_by_column`: diccionario con la cantidad de valores
      faltantes de cada columna. Considere faltantes las celdas vacías y las
      que contienen `N/A`.
    - `invalid_email_count`: cantidad de valores de `contact_email` que no
      tienen la forma `usuario@dominio.extension`.
    - `invalid_unit_count`: cantidad de valores numéricos de `units` que no son
      enteros positivos. Los valores faltantes no se cuentan aquí.
    - `country_values`: lista ordenada de los valores distintos de `country`,
      escritos exactamente como aparecen en el archivo.

    La función también debe retornar el reporte como un diccionario.

    Ejemplo del formato del reporte:

        {
          "row_count": 103,
          "column_count": 11,
          "missing_required_columns": [],
          ...
          "country_values": [" Colombia ", "CO", ...]
        }
    """

    # dtype=str y keep_default_na=False: todo se lee como texto, tal cual,
    # sin que Pandas convierta "N/A" o las celdas vacías en NaN.
    # encoding="utf-8-sig" quita la marca BOM del inicio del archivo.
    df = pd.read_csv(
        "data/ventas.csv.gz",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    # Normalización de encabezados: " Supplier ID " -> "supplier_id"
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    columnas_requeridas = [
        "supplier_id",
        "supplier",
        "country",
        "city",
        "purchase_date",
        "amount",
        "discount",
        "weight",
        "units",
        "unit_price",
        "contact_email",
    ]

    columnas_faltantes = []
    for columna in columnas_requeridas:
        if columna not in df.columns:
            columnas_faltantes.append(columna)

    columnas_inesperadas = []
    for columna in df.columns:
        if columna not in columnas_requeridas:
            columnas_inesperadas.append(columna)

    # Valores faltantes: celdas vacías o con el texto "N/A"
    faltantes_por_columna = {}
    for columna in df.columns:
        es_faltante = (df[columna] == "") | (df[columna] == "N/A")
        faltantes_por_columna[columna] = int(es_faltante.sum())

    # Correos inválidos: los que no tienen la forma usuario@dominio.extension
    correos_invalidos = 0
    for correo in df["contact_email"]:
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
            correos_invalidos += 1

    # Unidades inválidas: valores numéricos que no son enteros positivos
    unidades_invalidas = 0
    for valor in df["units"]:
        if valor == "" or valor == "N/A":
            continue

        try:
            numero = float(valor)
        except ValueError:
            # No es un número, así que no se cuenta aquí
            continue

        if numero <= 0 or not numero.is_integer():
            unidades_invalidas += 1

    reporte = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "missing_required_columns": sorted(columnas_faltantes),
        "unexpected_columns": sorted(columnas_inesperadas),
        # duplicated() marca las filas iguales a una fila anterior
        "duplicate_row_count": int(df.duplicated().sum()),
        # keep=False marca todas las filas del grupo repetido, no solo las copias
        "duplicate_supplier_id_row_count": int(
            df["supplier_id"].duplicated(keep=False).sum()
        ),
        "missing_value_count_by_column": faltantes_por_columna,
        "invalid_email_count": correos_invalidos,
        "invalid_unit_count": unidades_invalidas,
        "country_values": sorted(set(df["country"])),
    }

    os.makedirs("submission", exist_ok=True)
    with open("submission/data_quality_report.json", "w", encoding="utf-8") as archivo:
        json.dump(reporte, archivo, indent=2, ensure_ascii=False)

    return reporte
