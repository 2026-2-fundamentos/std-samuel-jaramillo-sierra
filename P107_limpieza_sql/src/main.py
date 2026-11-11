from pathlib import Path
import sqlite3

import pandas as pd

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = ACTIVITY_DIR / "data" / "ventas.csv"
OUTPUT_FILE = ACTIVITY_DIR / "submission" / "ventas.csv"
DATABASE_FILE = ACTIVITY_DIR / "temp" / "ventas.db"


def clean_column_names(df):
    # Casos tipicos en la columna
    # ' Supplier ID ' -> "supplier_id"
    # 'City ' -> "city"
    # 'Purchase Date' -> "purchase_date"
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    return df


def load_sales_table(connection):
    # dtype=str: todo se lee como texto ('0001' no pierde los ceros)
    # y la limpieza se hace con SQL.
    # row_id guarda el orden original de las filas.
    raw = pd.read_csv(INPUT_FILE, dtype=str)
    raw = clean_column_names(raw)
    raw.reset_index(names="row_id").to_sql(
        "sales", connection, if_exists="replace", index=False
    )


def clean_supplier_id_column(connection):
    # Casos tipicos en la columna
    # ' 0007 ' -> '0007'
    connection.execute("UPDATE sales SET supplier_id = TRIM(supplier_id)")


def clean_supplier_column(connection):
    connection.execute("UPDATE sales SET supplier = TRIM(supplier)")
    connection.execute(
        """
        UPDATE sales
        SET supplier = CASE
            WHEN supplier IN ('amazon web services colombia') THEN 'Amazon Web Services Colombia'
            WHEN supplier IN ('BANCOLOMBIA S.A.') THEN 'Bancolombia S.A.'
            WHEN supplier IN ('Cementos Argos SA', 'cementos argos s.a.') THEN 'Cementos Argos S.A.'
            WHEN supplier IN ('Corona SAS') THEN 'Corona S.A.S.'
            WHEN supplier IN ('Ecopetrol  S.A.') THEN 'Ecopetrol S.A.'
            WHEN supplier IN ('GOOGLE COLOMBIA LTDA.') THEN 'Google Colombia Ltda.'
            WHEN supplier IN ('Grupo  Éxito  S.A.') THEN 'Grupo Éxito S.A.'
            WHEN supplier IN ('IBM Colombia SAS.', 'ibm colombia s.a.s.') THEN 'IBM Colombia S.A.S.'
            WHEN supplier IN ('MICROSOFT COLOMBIA INC.') THEN 'Microsoft Colombia Inc.'
            WHEN supplier IN ('Nutresa SA', 'nutresa s.a.') THEN 'Nutresa S.A.'
            WHEN supplier IN ('oracle colombia ltda.') THEN 'Oracle Colombia Ltda.'
            WHEN supplier IN ('POSTOBÓN S.A.') THEN 'Postobon S.A.'
            WHEN supplier IN ('SAP Colombia SAS') THEN 'SAP Colombia S.A.S.'
            WHEN supplier IN ('Schneider  Electric') THEN 'Schneider Electric'
            WHEN supplier IN ('SIEMENS S.A.S.', 'siemens s.a.s.') THEN 'Siemens S.A.S.'
            WHEN supplier IN ('Sura  S.A.') THEN 'Sura S.A.'
            WHEN supplier IN ('Telefónica  Colombia') THEN 'Telefónica Colombia'
            ELSE supplier
        END
        """
    )


def clean_country_column(connection):
    connection.execute("UPDATE sales SET country = TRIM(country)")
    connection.execute(
        """
        UPDATE sales
        SET country = CASE
            WHEN country IN ('CO', 'COLOMBIA', 'Colombia', 'colombia') THEN 'COL'
            ELSE country
        END
        """
    )


def clean_city_column(connection):
    connection.execute("UPDATE sales SET city = TRIM(city)")
    connection.execute(
        """
        UPDATE sales
        SET city = CASE
            WHEN city IN ('bogotá', 'BOGOTÁ') THEN 'Bogotá'
            WHEN city IN ('Medellin', 'medellín', 'MEDELLÍN') THEN 'Medellín'
            ELSE city
        END
        """
    )


def clean_purchase_date_column(connection):
    # Casos tipicos en la columna
    # '2026/03/04' -> '2026-03-04'
    # '04/03/2026' -> '2026-03-04'  (el día primero)
    # '03/14/2026' -> '2026-03-14'  (el mes primero)
    # '04.03.2026' -> '2026-03-04'
    # '04-03-26'   -> '2026-03-04'
    #
    # GLOB revisa que el texto completo tenga esa forma ([0-9] es un dígito).
    # SUBSTR(texto, inicio, cantidad) saca un pedazo del texto y || los une.
    #
    # Igual que en P106: la fecha viene con el mes primero cuando el residuo
    # de supplier_id / 6 es 2, o cuando el número de la mitad es mayor que 12.
    connection.execute("UPDATE sales SET purchase_date = TRIM(purchase_date)")
    connection.execute(
        """
        UPDATE sales
        SET purchase_date = CASE
            WHEN purchase_date GLOB '[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]'
                THEN REPLACE(purchase_date, '/', '-')
            WHEN purchase_date GLOB '[0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9]'
                AND (
                    CAST(supplier_id AS INTEGER) % 6 = 2
                    OR CAST(SUBSTR(purchase_date, 4, 2) AS INTEGER) > 12
                )
                THEN SUBSTR(purchase_date, 7, 4) || '-' || SUBSTR(purchase_date, 1, 2) || '-' || SUBSTR(purchase_date, 4, 2)
            WHEN purchase_date GLOB '[0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9]'
                THEN SUBSTR(purchase_date, 7, 4) || '-' || SUBSTR(purchase_date, 4, 2) || '-' || SUBSTR(purchase_date, 1, 2)
            WHEN purchase_date GLOB '[0-9][0-9].[0-9][0-9].[0-9][0-9][0-9][0-9]'
                THEN SUBSTR(purchase_date, 7, 4) || '-' || SUBSTR(purchase_date, 4, 2) || '-' || SUBSTR(purchase_date, 1, 2)
            WHEN purchase_date GLOB '[0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
                THEN '20' || SUBSTR(purchase_date, 7, 2) || '-' || SUBSTR(purchase_date, 4, 2) || '-' || SUBSTR(purchase_date, 1, 2)
            ELSE purchase_date
        END
        """
    )


def clean_amount_column(connection):
    # Casos tipicos en la columna
    # '250.00K' -> '250000'
    # 'COP 1,250,000' -> '1250000'
    # '$1,250,000' -> '1250000'
    # '1.250.000' -> '1250000'
    connection.execute("UPDATE sales SET amount = TRIM(amount)")

    # La K significa miles
    connection.execute(
        """
        UPDATE sales
        SET amount = CAST(CAST(REPLACE(amount, 'K', '') AS REAL) * 1000 AS INTEGER)
        WHERE amount LIKE '%K'
        """
    )
    connection.execute(
        """
        UPDATE sales
        SET amount = TRIM(REPLACE(REPLACE(amount, 'COP', ''), ',', ''))
        WHERE amount LIKE 'COP%'
        """
    )
    connection.execute(
        """
        UPDATE sales
        SET amount = REPLACE(REPLACE(amount, '$', ''), ',', '')
        WHERE amount LIKE '$%'
        """
    )

    # Los puntos que quedan son separadores de miles
    connection.execute("UPDATE sales SET amount = REPLACE(amount, '.', '')")


def clean_discount_column(connection):
    # Casos tipicos en la columna
    # ' 20% ' -> 0.20
    # '5' -> 0.05
    # '0.05' -> 0.05
    #
    # SQLite guarda las columnas de este archivo como texto.
    # CAST(... AS REAL) convierte el texto en número para poder compararlo.
    connection.execute(
        "UPDATE sales SET discount = CAST(REPLACE(TRIM(discount), '%', '') AS REAL)"
    )

    # Los valores mayores que 1 están en porcentaje
    connection.execute(
        """
        UPDATE sales
        SET discount = CAST(discount AS REAL) / 100
        WHERE CAST(discount AS REAL) > 1
        """
    )


def clean_weight_column(connection):
    # Casos tipicos en la columna
    # '50000 g' -> 50.0
    # '0.0050 ton' -> 5.0
    # '2,5 kg' -> 2.5
    # '12' -> 12.0  (sin unidad, ya está en kilogramos)
    connection.execute("UPDATE sales SET weight = REPLACE(TRIM(weight), ',', '.')")
    connection.execute(
        """
        UPDATE sales
        SET weight = CASE
            WHEN weight LIKE '% ton' THEN CAST(REPLACE(weight, ' ton', '') AS REAL) * 1000
            WHEN weight LIKE '% kg' THEN CAST(REPLACE(weight, ' kg', '') AS REAL)
            WHEN weight LIKE '% g' THEN CAST(REPLACE(weight, ' g', '') AS REAL) / 1000
            ELSE CAST(weight AS REAL)
        END
        """
    )


def clean_unit_price_column(connection):
    # Casos tipicos en la columna
    # '96000.00' -> 96000.0
    # '980.000.00' -> 980000.0
    # '$1,050,000.00' -> 1050000.0
    # '$-1,750,000.00' -> 1750000.0
    connection.execute(
        "UPDATE sales SET unit_price = REPLACE(REPLACE(TRIM(unit_price), '$', ''), ',', '')"
    )

    # Los últimos 3 caracteres son los decimales ('.00').
    # En el resto del texto, los puntos son separadores de miles.
    connection.execute(
        """
        UPDATE sales
        SET unit_price = REPLACE(SUBSTR(unit_price, 1, LENGTH(unit_price) - 3), '.', '')
                         || SUBSTR(unit_price, -3)
        """
    )

    # Un precio no puede ser negativo: es un error de signo
    connection.execute("UPDATE sales SET unit_price = ABS(CAST(unit_price AS REAL))")


def clean_contact_email_column(connection):
    # 'sin correo' no es un correo: se deja vacío (NULL)
    connection.execute("UPDATE sales SET contact_email = TRIM(contact_email)")
    connection.execute(
        "UPDATE sales SET contact_email = NULL WHERE contact_email = 'sin correo'"
    )


def remove_duplicate_rows(connection):
    # Al final del archivo hay registros repetidos (0005, 0019 y 0010).
    # Después de limpiar quedan idénticos: se conserva solo la primera
    # aparición de cada uno (la del row_id más pequeño).
    connection.execute(
        """
        DELETE FROM sales
        WHERE row_id NOT IN (
            SELECT MIN(row_id)
            FROM sales
            GROUP BY
                supplier_id, supplier, country, city, purchase_date, amount,
                discount, weight, units, unit_price, contact_email
        )
        """
    )


def save_clean_sales(connection):
    # Las columnas numéricas se convierten a número al guardar el archivo.
    # units ya viene como número entero ('5', '12') y se deja igual.
    sales = pd.read_sql_query(
        """
        SELECT
            supplier_id,
            supplier,
            country,
            city,
            purchase_date,
            CAST(amount AS REAL) AS amount,
            CAST(discount AS REAL) AS discount,
            CAST(weight AS REAL) AS weight,
            units,
            CAST(unit_price AS REAL) AS unit_price,
            contact_email
        FROM sales
        ORDER BY row_id
        """,
        connection,
    )
    sales.to_csv(OUTPUT_FILE, index=False)


def main():
    connection = sqlite3.connect(DATABASE_FILE)
    load_sales_table(connection)
    clean_supplier_id_column(connection)
    clean_supplier_column(connection)
    clean_country_column(connection)
    clean_city_column(connection)
    clean_purchase_date_column(connection)
    clean_amount_column(connection)
    clean_discount_column(connection)
    clean_weight_column(connection)
    clean_unit_price_column(connection)
    clean_contact_email_column(connection)
    remove_duplicate_rows(connection)
    connection.commit()
    save_clean_sales(connection)
    connection.close()


if __name__ == "__main__":
    main()
