from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.ticker import PercentFormatter

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = ACTIVITY_DIR / "data" / "sales.csv.gz"
SUBMISSION_DIR = ACTIVITY_DIR / "submission"
CSV_FILE = SUBMISSION_DIR / "cohort_retention.csv"
PNG_FILE = SUBMISSION_DIR / "cohort_retention_heatmap.png"


def load_sales():
    df = pd.read_csv(INPUT_FILE)
    return df


def add_order_month_columns(df):
    # Casos tipicos en la columna OrderDate
    # '2022-04-21 01:48:37' -> order_month = '2022-04', month_number = 2022 * 12 + 4
    # month_number sirve para restar meses: abril - enero = 3 meses
    df["OrderDate"] = pd.to_datetime(df["OrderDate"])
    df["order_month"] = df["OrderDate"].dt.strftime("%Y-%m")
    df["month_number"] = df["OrderDate"].dt.year * 12 + df["OrderDate"].dt.month
    return df


def add_cohort_columns(df):
    # La cohorte de cada cliente es el mes de su primera compra
    # Casos tipicos
    # cliente con compras en 2022-01 y 2022-03 -> cohort_month = '2022-01'
    #   compra de 2022-01 -> period_index = 0
    #   compra de 2022-03 -> period_index = 2
    first_month_number = df.groupby("CustomerID")["month_number"].transform("min")
    df["cohort_month"] = df.groupby("CustomerID")["order_month"].transform("min")
    df["period_index"] = df["month_number"] - first_month_number
    return df


def build_retention_table(df):
    # Clientes distintos que compraron en cada cohorte y período
    retention = df.groupby(["cohort_month", "period_index"], as_index=False).agg(
        active_customers=("CustomerID", "nunique"),
    )

    # El tamaño de la cohorte son sus clientes activos en el período 0
    cohort_sizes = retention[retention["period_index"] == 0]
    cohort_sizes = cohort_sizes[["cohort_month", "active_customers"]]
    cohort_sizes = cohort_sizes.rename(columns={"active_customers": "cohort_size"})

    retention = retention.merge(
        cohort_sizes,
        on="cohort_month",
        how="left",
    )
    retention["retention_rate"] = (
        retention["active_customers"] / retention["cohort_size"]
    ).round(4)

    retention = retention.sort_values(["cohort_month", "period_index"])
    retention = retention[
        [
            "cohort_month",
            "period_index",
            "active_customers",
            "cohort_size",
            "retention_rate",
        ]
    ]
    return retention


def save_heatmap(retention):
    # Una fila por cohorte y una columna por período.
    # Los períodos que todavía no se pueden observar quedan como NaN,
    # y el mapa de calor los deja vacíos (no son retención cero)
    heatmap_data = retention.pivot(
        index="cohort_month",
        columns="period_index",
        values="retention_rate",
    )

    plt.figure(figsize=(10, 6))
    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt=".0%",
        cmap="Blues",
        vmin=0,
        vmax=1,
        cbar_kws={"format": PercentFormatter(xmax=1)},
    )
    plt.title("Retención de clientes por cohorte")
    plt.xlabel("Meses desde la primera compra (period_index)")
    plt.ylabel("Cohorte (mes de la primera compra)")
    plt.tight_layout()
    plt.savefig(PNG_FILE)
    plt.close()


def build_cohort_analysis() -> pd.DataFrame:
    """
    Una tienda quiere saber si sus clientes vuelven a comprar después de su
    primera compra. Para responder, agrupe a los clientes en cohortes según
    el mes de su primera compra y mida, mes a mes, qué proporción de cada
    cohorte vuelve a comprar. Use `data/sales.csv.gz`, que tiene una fila por
    orden con su cliente (`CustomerID`) y su fecha (`OrderDate`).

    Use estas definiciones:

    - `cohort_month`: el mes de la primera compra del cliente, escrito como
      `AAAA-MM`.
    - `period_index`: los meses transcurridos desde `cohort_month`; es 0 en el
      mes de la primera compra, 1 en el mes siguiente, y así sucesivamente.
    - `active_customers`: la cantidad de clientes distintos de la cohorte que
      compraron en ese período.
    - `cohort_size`: la cantidad de clientes de la cohorte, es decir, sus
      clientes activos en el período 0.
    - `retention_rate`: `active_customers` sobre `cohort_size`.

    Genere dos archivos en `submission/`:

    1. `cohort_retention.csv`, sin el índice de Pandas, con las columnas
       `cohort_month`, `period_index`, `active_customers`, `cohort_size` y
       `retention_rate`, y una fila por cada combinación cohorte–período
       observada, ordenadas por cohorte y período.

    2. `cohort_retention_heatmap.png`, un mapa de calor de `retention_rate`
       con una fila por cohorte (eje vertical) y una columna por período
       (eje horizontal). Muestre los valores como porcentajes. Los períodos
       que todavía no se pueden observar para una cohorte no significan
       retención cero: déjelos vacíos en el mapa.

    La función también debe retornar la tabla de retención.

    Ejemplo del formato de `cohort_retention.csv`:

        cohort_month,period_index,active_customers,cohort_size,retention_rate
        2022-01,0,100,100,1.0
        2022-01,1,26,100,0.26
        ...
    """

    df = load_sales()
    df = add_order_month_columns(df)
    df = add_cohort_columns(df)
    retention = build_retention_table(df)

    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    retention.to_csv(CSV_FILE, index=False)
    save_heatmap(retention)

    return retention
