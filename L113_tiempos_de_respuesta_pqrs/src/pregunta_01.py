from pathlib import Path

import numpy as np
import pandas as pd

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ACTIVITY_DIR / "data"
SUBMISSION_DIR = ACTIVITY_DIR / "submission"

INPUT_FILES = {
    "letter": DATA_DIR / "historical_requests_letter.csv.gz",
    "web": DATA_DIR / "historical_requests_web.csv.gz",
}

MAX_BUSINESS_DAYS = 15

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def load_requests():
    # Se lee cada canal, se quitan sus filas idénticas y se juntan los dos.
    # Las filas sin record_id se conservan: son solicitudes válidas
    tables = []
    for channel, input_file in INPUT_FILES.items():
        df = pd.read_csv(input_file)
        df = df.drop_duplicates()
        df["channel"] = channel
        tables.append(df)

    df = pd.concat(tables, ignore_index=True)
    return df


def convert_date_columns(df):
    # Casos tipicos
    # in_date = '2016-01-01' -> fecha
    # out_date vacío -> NaT (la solicitud está pendiente)
    df["in_date"] = pd.to_datetime(df["in_date"])
    df["out_date"] = pd.to_datetime(df["out_date"])
    df["year"] = df["in_date"].dt.year
    df["answered"] = df["out_date"].notna()
    return df


def add_calendar_days_column(df):
    # Diferencia entre la fecha de respuesta y la de entrada
    # Casos tipicos
    # 2016-01-01 -> 2016-01-10 = 9 días calendario
    # pendiente -> NaN
    df["calendar_days"] = (df["out_date"] - df["in_date"]).dt.days
    return df


def add_business_days_column(df):
    # Días de lunes a viernes después de la entrada y hasta la respuesta incluida.
    # np.busday_count(inicio, fin) cuenta los días hábiles desde inicio hasta
    # fin SIN incluir fin; por eso a las dos fechas se les suma un día.
    # Casos tipicos
    # entra viernes 2016-01-01, responde lunes 2016-01-04 -> 1 día hábil
    # entra sábado 2016-01-02, responde lunes 2016-01-11 -> 6 días hábiles
    # pendiente -> NaN
    answered = df[df["answered"]]
    one_day = pd.Timedelta(days=1)
    start_dates = (answered["in_date"] + one_day).to_numpy(dtype="datetime64[D]")
    end_dates = (answered["out_date"] + one_day).to_numpy(dtype="datetime64[D]")

    df["business_days"] = np.nan
    df.loc[df["answered"], "business_days"] = np.busday_count(start_dates, end_dates)
    return df


def add_on_time_column(df):
    # Cumple si fue respondida en 15 días hábiles o menos.
    # Una pendiente tiene business_days = NaN, y NaN <= 15 da False: no cumple
    df["on_time"] = df["business_days"] <= MAX_BUSINESS_DAYS
    return df


def build_channel_summary(df):
    # Una fila por canal; groupby ya los deja en orden alfabético
    summary = df.groupby("channel", as_index=False).agg(
        requests=("in_date", "size"),
        answered=("answered", "sum"),
        median_business_days=("business_days", "median"),
        on_time_rate=("on_time", "mean"),
    )
    summary["pending"] = summary["requests"] - summary["answered"]
    summary = summary[
        [
            "channel",
            "requests",
            "answered",
            "pending",
            "median_business_days",
            "on_time_rate",
        ]
    ]
    return summary


def build_yearly_summary(df):
    # Una fila por año y canal, ordenada por año y luego por canal
    summary = df.groupby(["year", "channel"], as_index=False).agg(
        requests=("in_date", "size"),
        answered=("answered", "sum"),
        on_time_rate=("on_time", "mean"),
    )
    summary["pending"] = summary["requests"] - summary["answered"]
    summary = summary.sort_values(["year", "channel"])
    summary = summary[
        [
            "year",
            "channel",
            "requests",
            "pending",
            "on_time_rate",
        ]
    ]
    return summary


def build_entry_day_summary(df):
    # Una fila por día de entrada, con los dos canales juntos.
    # La mediana ignora los NaN, así que solo usa las solicitudes respondidas
    summary = df.groupby("day_name", as_index=False).agg(
        requests=("in_date", "size"),
        median_calendar_days=("calendar_days", "median"),
        median_business_days=("business_days", "median"),
    )

    # Se ordena de lunes a domingo
    summary = summary.set_index("day_name")
    summary = summary.loc[DAY_NAMES]
    summary = summary.reset_index()

    summary = summary[
        [
            "day_name",
            "requests",
            "median_calendar_days",
            "median_business_days",
        ]
    ]
    return summary


def save_table(table, file_name):
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(SUBMISSION_DIR / file_name, index=False)


def pregunta_01() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Una entidad pública recibe peticiones, quejas, reclamos y sugerencias
    (PQRS) por dos canales, la página web y las cartas, y la ley le da 15 días
    hábiles para responder cada una. Su tarea es medir si la entidad cumple
    ese plazo.

    Los archivos `data/historical_requests_web.csv.gz` y
    `data/historical_requests_letter.csv.gz` tienen una fila por solicitud
    recibida entre 2016 y 2021 por cada canal, con su identificador
    (`record_id`), la fecha de entrada (`in_date`), el día de la semana de
    entrada (`day_name`) y la fecha de respuesta (`out_date`). Si `out_date`
    está vacía, la solicitud todavía no ha sido respondida.

    Tenga en cuenta lo siguiente:

    - Algunas solicitudes aparecen repetidas: elimine las filas idénticas
      dentro de cada canal, para contar cada solicitud una sola vez. Las
      filas sin `record_id` son solicitudes válidas.
    - Llame `letter` al canal de las cartas y `web` al de la página web.
    - Los días hábiles de respuesta son los días de lunes a viernes
      posteriores a la fecha de entrada, hasta la fecha de respuesta
      incluida. Por ejemplo, una solicitud que entra un viernes y se responde
      el lunes siguiente tardó 1 día hábil. No considere los festivos.
    - Los días calendario de respuesta son la diferencia entre la fecha de
      respuesta y la de entrada.
    - Una solicitud cumple el plazo si fue respondida en 15 días hábiles o
      menos. Una solicitud pendiente no ha cumplido el plazo.
    - `on_time_rate` es la proporción de solicitudes que cumplen el plazo,
      sobre el total de solicitudes, incluidas las pendientes.
    - Las medianas de días se calculan solamente con las solicitudes
      respondidas.

    Genere tres archivos en `submission/`, sin el índice de Pandas y con las
    columnas en el orden indicado:

    1. `channel_summary.csv`, con una fila por canal, en orden alfabético:
       `channel`, `requests`, `answered`, `pending`,
       `median_business_days` y `on_time_rate`.

    2. `yearly_summary.csv`, con una fila por año de entrada y canal,
       ordenada por año y luego por canal: `year`, `channel`, `requests`,
       `pending` y `on_time_rate`.

    3. `entry_day_summary.csv`, con una fila por día de entrada, de lunes a
       domingo, con los dos canales juntos: `day_name`, `requests`,
       `median_calendar_days` y `median_business_days`.

    Observe en el tercer archivo cómo cambia la lectura del tiempo de
    respuesta según se cuenten días calendario o días hábiles.

    La función también debe retornar las tres tablas, en el mismo orden.

    Ejemplo del formato de `channel_summary.csv`:

        channel,requests,answered,pending,median_business_days,on_time_rate
        letter,28138,...
        ...
    """

    df = load_requests()
    df = convert_date_columns(df)
    df = add_calendar_days_column(df)
    df = add_business_days_column(df)
    df = add_on_time_column(df)

    # Los resultados se redondean a 4 decimales
    channel_summary = build_channel_summary(df).round(4)
    yearly_summary = build_yearly_summary(df).round(4)
    entry_day_summary = build_entry_day_summary(df).round(4)

    save_table(channel_summary, "channel_summary.csv")
    save_table(yearly_summary, "yearly_summary.csv")
    save_table(entry_day_summary, "entry_day_summary.csv")

    return channel_summary, yearly_summary, entry_day_summary
