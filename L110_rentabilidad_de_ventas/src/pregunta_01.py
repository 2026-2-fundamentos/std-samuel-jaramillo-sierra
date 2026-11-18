from pathlib import Path

import pandas as pd

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = ACTIVITY_DIR / "data" / "superstore_orders.csv.gz"
SUBMISSION_DIR = ACTIVITY_DIR / "submission"

DISCOUNT_BANDS = ["0%", "1%-5%", "6%-10%", "más de 10%"]

MIN_SEGMENT_LINES = 100


def load_orders():
    # El archivo usa ";" como separador, "," como decimal y trae BOM al inicio
    # Casos tipicos en la columna Profit
    # '4,56' -> 4.56
    # '-53,8096' -> -53.8096
    df = pd.read_csv(
        INPUT_FILE,
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
    )
    return df


def add_loss_columns(df):
    # Una línea con pérdida es la que tiene utilidad negativa.
    # lost_profit guarda esa pérdida como número positivo (0 si no hubo pérdida)
    # Casos tipicos
    # Profit = 4.56 -> loss_line = False, lost_profit = 0.0
    # Profit = -53.8096 -> loss_line = True, lost_profit = 53.8096
    df["loss_line"] = df["Profit"] < 0
    df["lost_profit"] = 0.0
    df.loc[df["loss_line"], "lost_profit"] = -df["Profit"]
    return df


def add_discount_band_column(df):

    def convert_value(value):
        # Casos tipicos en la columna Discount
        # 0.00 -> "0%"
        # 0.03 -> "1%-5%"
        # 0.08 -> "6%-10%"
        # 0.17 -> "más de 10%"
        if value == 0:
            return "0%"
        if value <= 0.05:
            return "1%-5%"
        if value <= 0.10:
            return "6%-10%"
        return "más de 10%"

    df["discount_band"] = df["Discount"].apply(convert_value)
    return df


def add_rates(summary):
    # Margen: utilidad sobre ventas
    summary["profit_margin"] = summary["profit"] / summary["sales"]
    # Proporción de líneas con pérdida
    summary["loss_line_rate"] = summary["loss_lines"] / summary["lines"]
    return summary


def build_profitability_summary(df):
    # Una sola fila con los totales de todas las líneas
    summary = pd.DataFrame(
        {
            "lines": [len(df)],
            "orders": [df["Order ID"].nunique()],
            "sales": [df["Sales"].sum()],
            "profit": [df["Profit"].sum()],
            "loss_lines": [df["loss_line"].sum()],
            "lost_profit": [df["lost_profit"].sum()],
        }
    )
    summary = add_rates(summary)
    summary = summary[
        [
            "lines",
            "orders",
            "sales",
            "profit",
            "profit_margin",
            "loss_lines",
            "loss_line_rate",
            "lost_profit",
        ]
    ]
    return summary


def build_discount_summary(df):
    # Una fila por rango de descuento
    summary = df.groupby("discount_band", as_index=False).agg(
        lines=("Profit", "count"),
        sales=("Sales", "sum"),
        profit=("Profit", "sum"),
        loss_lines=("loss_line", "sum"),
        lost_profit=("lost_profit", "sum"),
    )
    summary = add_rates(summary)

    # Se ordena en el mismo orden en que se definieron los rangos
    summary = summary.set_index("discount_band")
    summary = summary.loc[DISCOUNT_BANDS]
    summary = summary.reset_index()

    summary = summary[
        [
            "discount_band",
            "lines",
            "sales",
            "profit",
            "profit_margin",
            "loss_line_rate",
            "lost_profit",
        ]
    ]
    return summary


def build_priority_segments(df):
    # Una fila por cada combinación segmento-categoría
    summary = df.groupby(
        ["Customer Segment", "Product Category"],
        as_index=False,
    ).agg(
        lines=("Profit", "count"),
        sales=("Sales", "sum"),
        profit=("Profit", "sum"),
        loss_lines=("loss_line", "sum"),
        lost_profit=("lost_profit", "sum"),
    )
    summary = add_rates(summary)

    # Solo segmentos con al menos 100 líneas, y los 5 que más utilidad pierden
    summary = summary[summary["lines"] >= MIN_SEGMENT_LINES]
    summary = summary.sort_values("lost_profit", ascending=False)
    summary = summary.head(5)

    summary = summary[
        [
            "Customer Segment",
            "Product Category",
            "lines",
            "sales",
            "profit",
            "profit_margin",
            "lost_profit",
        ]
    ]
    return summary


def save_table(table, file_name):
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(SUBMISSION_DIR / file_name, index=False)


def pregunta_01() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Una cadena de suministros de oficina vende mucho, pero la gerencia
    sospecha que parte de esas ventas no deja utilidad. El archivo
    `data/superstore_orders.csv.gz` tiene una fila por línea de pedido, con
    el número de pedido (`Order ID`), las ventas (`Sales`), la utilidad
    (`Profit`), el descuento aplicado (`Discount`, como proporción), el
    segmento del cliente (`Customer Segment`) y la categoría del producto
    (`Product Category`). Una utilidad negativa significa que la línea se
    vendió con pérdida.

    Use estas definiciones:

    - Margen (`profit_margin`): utilidad sobre ventas.
    - Línea con pérdida: una línea cuya utilidad es negativa.
    - `loss_line_rate`: la proporción de líneas con pérdida.
    - `lost_profit`: la suma de las pérdidas de las líneas con pérdida,
      escrita como número positivo.
    - Rango de descuento (`discount_band`): `0%` si no hubo descuento,
      `1%-5%` si fue mayor que 0 y hasta 5 %, `6%-10%` si fue mayor que 5 % y
      hasta 10 %, y `más de 10%` en otro caso.

    Genere tres archivos en `submission/`, sin el índice de Pandas y con las
    columnas en el orden indicado:

    1. `profitability_summary.csv`, con una sola fila: `lines` (cantidad de
       líneas), `orders` (pedidos distintos), `sales`, `profit`,
       `profit_margin`, `loss_lines` (cantidad de líneas con pérdida),
       `loss_line_rate` y `lost_profit`.

    2. `discount_summary.csv`, con una fila por rango de descuento, en el
       orden en que se definieron arriba: `discount_band`, `lines`, `sales`,
       `profit`, `profit_margin`, `loss_line_rate` y `lost_profit`.

    3. `priority_segments.csv`, con los cinco segmentos segmento–categoría
       que más utilidad pierden: `Customer Segment`, `Product Category`,
       `lines`, `sales`, `profit`, `profit_margin` y `lost_profit`. Considere
       solamente segmentos con al menos 100 líneas y ordénelos por
       `lost_profit` de mayor a menor.

    La función también debe retornar las tres tablas, en el mismo orden.

    Ejemplo del formato de `discount_summary.csv`:

        discount_band,lines,sales,profit,profit_margin,loss_line_rate,...
        0%,166,170539.05,29472.3789,0.1728,0.488,...
        ...
    """

    df = load_orders()
    df = add_loss_columns(df)
    df = add_discount_band_column(df)

    # Los resultados se redondean a 4 decimales, como en el ejemplo
    profitability_summary = build_profitability_summary(df).round(4)
    discount_summary = build_discount_summary(df).round(4)
    priority_segments = build_priority_segments(df).round(4)

    save_table(profitability_summary, "profitability_summary.csv")
    save_table(discount_summary, "discount_summary.csv")
    save_table(priority_segments, "priority_segments.csv")

    return profitability_summary, discount_summary, priority_segments
