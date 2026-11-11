from pathlib import Path

import pandas as pd

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = ACTIVITY_DIR / "data" / "ventas.csv"
OUTPUT_FILE = ACTIVITY_DIR / "submission" / "ventas.csv"

SUPPLIER_REPLACEMENTS = {
    "amazon web services colombia": "Amazon Web Services Colombia",
    "BANCOLOMBIA S.A.": "Bancolombia S.A.",
    "Cementos Argos SA": "Cementos Argos S.A.",
    "cementos argos s.a.": "Cementos Argos S.A.",
    "Corona SAS": "Corona S.A.S.",
    "Ecopetrol  S.A.": "Ecopetrol S.A.",
    "GOOGLE COLOMBIA LTDA.": "Google Colombia Ltda.",
    "Grupo  Éxito  S.A.": "Grupo Éxito S.A.",
    "IBM Colombia SAS.": "IBM Colombia S.A.S.",
    "ibm colombia s.a.s.": "IBM Colombia S.A.S.",
    "MICROSOFT COLOMBIA INC.": "Microsoft Colombia Inc.",
    "Nutresa SA": "Nutresa S.A.",
    "nutresa s.a.": "Nutresa S.A.",
    "oracle colombia ltda.": "Oracle Colombia Ltda.",
    "POSTOBÓN S.A.": "Postobon S.A.",
    "SAP Colombia SAS": "SAP Colombia S.A.S.",
    "Schneider  Electric": "Schneider Electric",
    "SIEMENS S.A.S.": "Siemens S.A.S.",
    "siemens s.a.s.": "Siemens S.A.S.",
    "Sura  S.A.": "Sura S.A.",
    "Telefónica  Colombia": "Telefónica Colombia",
}


COUNTRY_REPLACEMENTS = {
    "CO": "COL",
    "COLOMBIA": "COL",
    "Colombia": "COL",
    "colombia": "COL",
}

CITY_REPLACEMENTS = {
    "bogotá": "Bogotá",
    "BOGOTÁ": "Bogotá",
    "Medellin": "Medellín",
    "medellín": "Medellín",
    "MEDELLÍN": "Medellín",
}


def clean_column_names(df):
    # Casos tipicos en la columna
    # ' Supplier ID ' -> "supplier_id"
    # 'City ' -> "city"
    # 'Purchase Date' -> "purchase_date"
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df


def clean_supplier_id_column(df):
    # pandas lee ' 0007 ' como el número 7 y se pierden los ceros.
    # zfill(4) rellena con ceros a la izquierda hasta tener 4 caracteres.
    # 7 -> '0007'
    df["supplier_id"] = df["supplier_id"].astype(str).str.strip().str.zfill(4)
    return df


def clean_supplier_column(df):
    df["supplier"] = df["supplier"].str.strip()
    df["supplier"] = df["supplier"].replace(SUPPLIER_REPLACEMENTS)
    return df


def clean_country_column(df):
    df["country"] = df["country"].str.strip()
    df["country"] = df["country"].replace(COUNTRY_REPLACEMENTS)
    return df


def clean_city_column(df):
    df["city"] = df["city"].str.strip()
    df["city"] = df["city"].replace(CITY_REPLACEMENTS)
    return df


def clean_purchase_date_column(df):

    def convert_yyyy_s_mm_s_dd_to_yyyy_mm_dd(series):
        # Convierte fechas en formato "YYYY/MM/DD" a "YYYY-MM-DD"
        series = series.str.replace(r"(\d{4})/(\d{2})/(\d{2})", r"\1-\2-\3", regex=True)
        return series

    def convert_mm_s_dd_s_yyyy_to_yyyy_mm_dd(series):
        # Convierte fechas en formato "MM/DD/YYYY" a "YYYY-MM-DD"
        series = series.str.replace(r"(\d{2})/(\d{2})/(\d{4})", r"\3-\1-\2", regex=True)
        return series

    def convert_mmddyyyy_to_yyyy_mm_dd(series):
        # Corrige solo fechas con el día primero, cuando el día es mayor que 12.
        def convert_date(match):
            g1, g2, g3 = match.groups()
            if int(g2) > 12:  # el dia aparece en la mitad
                return f"{g3}-{g1}-{g2}"
            return f"{g3}-{g2}-{g1}"

        return series.str.replace(r"(\d{2})/(\d{2})/(\d{4})", convert_date, regex=True)

    def convert_dd_mm_yy_to_yyyy_mm_dd(series):
        # Convierte fechas en formato "DD-MM-YY" a "YYYY-MM-DD" (el año es 20YY)
        # ^ y $ evitan que el patrón encuentre "26-07-07" dentro de "2026-07-07"
        series = series.str.replace(r"^(\d{2})-(\d{2})-(\d{2})$", r"20\3-\2-\1", regex=True)
        return series

    def convert_dd_p_mm_p_yyyy_to_yyyy_mm_dd(series):
        # Convierte fechas en formato "DD.MM.YYYY" a "YYYY-MM-DD"
        series = series.str.replace(r"(\d{2})\.(\d{2})\.(\d{4})", r"\3-\2-\1", regex=True)
        return series

    # Patrón de los datos: el formato de la fecha se repite cada 6 registros
    # según el supplier_id. Cuando el residuo de supplier_id / 6 es 2, la
    # fecha viene como "MM/DD/YYYY" (el mes primero).
    is_mm_dd_yyyy = df["supplier_id"].astype(int) % 6 == 2

    df["purchase_date"] = df["purchase_date"].str.strip()
    df["purchase_date"] = convert_yyyy_s_mm_s_dd_to_yyyy_mm_dd(df["purchase_date"])
    df.loc[is_mm_dd_yyyy, "purchase_date"] = convert_mm_s_dd_s_yyyy_to_yyyy_mm_dd(
        df.loc[is_mm_dd_yyyy, "purchase_date"]
    )
    df["purchase_date"] = convert_mmddyyyy_to_yyyy_mm_dd(df["purchase_date"])
    df["purchase_date"] = convert_dd_mm_yy_to_yyyy_mm_dd(df["purchase_date"])
    df["purchase_date"] = convert_dd_p_mm_p_yyyy_to_yyyy_mm_dd(df["purchase_date"])
    return df


def clean_discount_column(df):
    # Casos tipicos en la columna
    # ' 20% ' -> 0.20
    # '5' -> 0.05
    # '0.05' -> 0.05
    df["discount"] = df["discount"].str.strip()
    df["discount"] = df["discount"].str.replace("%", "")
    df["discount"] = df["discount"].astype(float)

    # Los valores mayores que 1 están en porcentaje
    is_percentage = df["discount"] > 1
    df.loc[is_percentage, "discount"] = df.loc[is_percentage, "discount"] / 100
    return df


def clean_weight_column(df):

    def convert_to_kg(match):
        # Pasa el peso a kilogramos según la unidad.
        # Si no tiene unidad, el número ya está en kilogramos.
        number, unit = match.groups()
        number = float(number)
        if unit == "g":
            number = number / 1000
        if unit == "ton":
            number = number * 1000
        return str(number)

    # Casos tipicos en la columna
    # '50000 g' -> 50.0
    # '0.0050 ton' -> 5.0
    # '2,5 kg' -> 2.5
    # '12' -> 12.0
    df["weight"] = df["weight"].str.strip()
    df["weight"] = df["weight"].str.replace(",", ".")
    df["weight"] = df["weight"].str.replace(r"^([\d.]+)\s*(g|kg|ton)?$", convert_to_kg, regex=True)
    df["weight"] = df["weight"].astype(float)
    return df


def clean_amount_column(df):

    def remove_thousands_dots(match):
        # '1.250.000' -> '1250000'
        return match.group(0).replace(".", "")

    def convert_k_to_number(match):
        # La K significa miles: '250.00K' -> '250000.0'
        number = float(match.group(1))
        return str(number * 1000)

    # Casos tipicos en la columna
    # '$480,000' -> 480000.0
    # 'COP 1,250,000' -> 1250000.0
    # '1.250.000' -> 1250000.0
    # '250.00K' -> 250000.0
    df["amount"] = df["amount"].str.replace("$", "")
    df["amount"] = df["amount"].str.replace("COP", "")
    df["amount"] = df["amount"].str.strip()
    df["amount"] = df["amount"].str.replace(",", "")
    df["amount"] = df["amount"].str.replace(r"^\d{1,3}(\.\d{3})+$", remove_thousands_dots, regex=True)
    df["amount"] = df["amount"].str.replace(r"^([\d.]+)K$", convert_k_to_number, regex=True)
    df["amount"] = df["amount"].astype(float)
    return df


def clean_units_column(df):
    # pandas lee la columna como decimal (5.0) porque tiene valores vacíos.
    # "Int64" (con I mayúscula) es un entero que sí acepta vacíos: 5.0 -> 5
    df["units"] = df["units"].astype("Int64")
    return df


def clean_unit_price_column(df):

    def convert_unit_price(match):
        # Los puntos de la parte entera son separadores de miles.
        # Solo el último punto separa los decimales.
        # '1.250.000.00' -> '1250000.00'
        integer_part, decimal_part = match.groups()
        integer_part = integer_part.replace(".", "")
        return integer_part + "." + decimal_part

    # Casos tipicos en la columna
    # '96000.00' -> 96000.0
    # '980.000.00' -> 980000.0
    # '$1,050,000.00' -> 1050000.0
    # '$-1,750,000.00' -> 1750000.0
    df["unit_price"] = df["unit_price"].str.strip()
    df["unit_price"] = df["unit_price"].str.replace("$", "")
    df["unit_price"] = df["unit_price"].str.replace(",", "")
    df["unit_price"] = df["unit_price"].str.replace(r"^(-?[\d.]+)\.(\d{2})$", convert_unit_price, regex=True)
    df["unit_price"] = df["unit_price"].astype(float)

    # Un precio no puede ser negativo: es un error de signo
    # (amount / units da el mismo valor, pero positivo)
    df["unit_price"] = df["unit_price"].abs()
    return df


def clean_contact_email_column(df):
    # 'sin correo' no es un correo: se deja vacío
    df["contact_email"] = df["contact_email"].str.strip()
    has_no_email = df["contact_email"] == "sin correo"
    df.loc[has_no_email, "contact_email"] = None
    return df


def remove_duplicate_rows(df):
    # Al final del archivo hay registros repetidos (0005, 0019 y 0010).
    # Después de limpiar quedan idénticos, así que se pueden eliminar.
    df = df.drop_duplicates()
    return df


def main():
    df = pd.read_csv(INPUT_FILE)
    df = clean_column_names(df)
    df = clean_supplier_id_column(df)
    df = clean_supplier_column(df)
    df = clean_country_column(df)
    df = clean_city_column(df)
    df = clean_purchase_date_column(df)
    df = clean_discount_column(df)
    df = clean_weight_column(df)
    df = clean_amount_column(df)
    df = clean_units_column(df)
    df = clean_unit_price_column(df)
    df = clean_contact_email_column(df)
    df = remove_duplicate_rows(df)
    df.to_csv(OUTPUT_FILE, index=False)


if __name__ == "__main__":
    main()
