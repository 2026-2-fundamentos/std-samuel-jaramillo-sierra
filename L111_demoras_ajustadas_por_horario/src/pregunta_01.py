from pathlib import Path

import pandas as pd

ACTIVITY_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = ACTIVITY_DIR / "data" / "flights_by_carrier_day_hour.csv.gz"
SUBMISSION_DIR = ACTIVITY_DIR / "submission"

MIN_OPERATED_FLIGHTS = 100_000


def load_flights():
    df = pd.read_csv(INPUT_FILE)
    return df


def build_hourly_delay_rates(df):
    # Paso 1: tasa nacional de demora de cada hora, con todas las aerolíneas juntas
    # Casos tipicos
    # hora 6 -> 92846 demorados / 1477488 operados = 0.0628
    # hora 19 -> 368607 demorados / 1210173 operados = 0.3046
    hourly = df.groupby("scheduled_departure_hour", as_index=False).agg(
        operated_flights=("operated_flights", "sum"),
        delayed_departure_15_flights=("delayed_departure_15_flights", "sum"),
    )
    hourly["operated_flights"] = hourly["operated_flights"].astype(int)
    hourly["delayed_departure_15_flights"] = hourly[
        "delayed_departure_15_flights"
    ].astype(int)
    hourly["delay_rate"] = (
        hourly["delayed_departure_15_flights"] / hourly["operated_flights"]
    )
    return hourly


def add_expected_delays(df, hourly):
    # Paso 2: a cada fila se le pega la tasa nacional de su hora, y las demoras
    # esperadas son sus vuelos operados por esa tasa
    national_rates = hourly[["scheduled_departure_hour", "delay_rate"]]
    national_rates = national_rates.rename(
        columns={"delay_rate": "national_delay_rate"}
    )

    df = df.merge(
        national_rates,
        on="scheduled_departure_hour",
        how="left",
    )
    df["expected_delayed_flights"] = (
        df["operated_flights"] * df["national_delay_rate"]
    )
    return df


def build_carrier_adjusted_delays(df):
    # Se suman las horas de cada aerolínea
    carriers = df.groupby("reporting_airline", as_index=False).agg(
        operated_flights=("operated_flights", "sum"),
        delayed_departure_15_flights=("delayed_departure_15_flights", "sum"),
        expected_delayed_flights=("expected_delayed_flights", "sum"),
    )
    carriers["operated_flights"] = carriers["operated_flights"].astype(int)
    carriers["delayed_departure_15_flights"] = carriers[
        "delayed_departure_15_flights"
    ].astype(int)

    # Solo aerolíneas con al menos 100 000 vuelos operados
    carriers = carriers[carriers["operated_flights"] >= MIN_OPERATED_FLIGHTS]
    carriers = carriers.copy()

    # Tasa sin ajustar
    carriers["delay_rate"] = (
        carriers["delayed_departure_15_flights"] / carriers["operated_flights"]
    )

    # Paso 3: demoras observadas sobre esperadas
    # Mayor que 1 -> se demora más de lo que explican sus horarios
    carriers["observed_to_expected_ratio"] = (
        carriers["delayed_departure_15_flights"] / carriers["expected_delayed_flights"]
    )

    # Rankings: 1 es la peor aerolínea (la de valor más alto)
    carriers["crude_rank"] = (
        carriers["delay_rate"].rank(ascending=False, method="first").astype(int)
    )
    carriers["adjusted_rank"] = (
        carriers["observed_to_expected_ratio"]
        .rank(ascending=False, method="first")
        .astype(int)
    )

    carriers = carriers.sort_values("adjusted_rank")
    carriers = carriers[
        [
            "reporting_airline",
            "operated_flights",
            "delayed_departure_15_flights",
            "delay_rate",
            "expected_delayed_flights",
            "observed_to_expected_ratio",
            "crude_rank",
            "adjusted_rank",
        ]
    ]
    return carriers


def save_table(table, file_name):
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(SUBMISSION_DIR / file_name, index=False)


def pregunta_01() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Una autoridad aeronáutica publica cada año un ranking de aerolíneas según
    su tasa de demora, y algunas aerolíneas se quejan de que es injusto: las
    demoras se acumulan a lo largo del día, de modo que una aerolínea con
    muchos vuelos en la tarde y la noche parece peor aunque opere igual de
    bien que las demás. Su tarea es construir un ranking que tenga en cuenta
    la mezcla de horarios de cada aerolínea.

    El archivo `data/flights_by_carrier_day_hour.csv.gz` tiene los vuelos
    nacionales entre 2006 y 2008, agregados por año, mes, día de la semana,
    hora programada de salida (`scheduled_departure_hour`) y aerolínea
    (`reporting_airline`). Use las columnas `operated_flights` (vuelos
    operados) y `delayed_departure_15_flights` (vuelos que salieron con 15
    minutos o más de demora).

    Siga estos pasos:

    1. Calcule la tasa nacional de demora de cada hora programada de salida:
       vuelos demorados sobre vuelos operados, con todas las aerolíneas
       juntas.
    2. Para cada aerolínea, calcule las demoras esperadas: en cada hora,
       multiplique sus vuelos operados por la tasa nacional de esa hora, y
       sume sobre todas las horas. Son las demoras que tendría si en cada hora
       se comportara como el promedio nacional.
    3. Divida las demoras observadas entre las esperadas. Un valor mayor que 1
       significa que la aerolínea se demora más de lo que explican sus
       horarios.

    Genere dos archivos en `submission/`, sin el índice de Pandas y con las
    columnas en el orden indicado:

    1. `hourly_delay_rates.csv`, con una fila por hora, de 0 a 23:
       `scheduled_departure_hour`, `operated_flights`,
       `delayed_departure_15_flights` y `delay_rate`.

    2. `carrier_adjusted_delays.csv`, con una fila por aerolínea:
       `reporting_airline`, `operated_flights`,
       `delayed_departure_15_flights`, `delay_rate` (la tasa sin ajustar),
       `expected_delayed_flights`, `observed_to_expected_ratio`, `crude_rank`
       y `adjusted_rank`. Incluya solamente aerolíneas con al menos 100 000
       vuelos operados. `crude_rank` es la posición según `delay_rate` y
       `adjusted_rank` la posición según `observed_to_expected_ratio`; en
       ambos, 1 es la peor aerolínea. Ordene la tabla por `adjusted_rank`.

    Compare los dos rankings: las aerolíneas que cambian de posición son las
    que el ranking sin ajustar juzga mal por sus horarios.

    La función también debe retornar las dos tablas, en el mismo orden.

    Ejemplo del formato de `carrier_adjusted_delays.csv`:

        reporting_airline,operated_flights,...,crude_rank,adjusted_rank
        EV,819223,...,1,1
        ...
    """

    df = load_flights()
    hourly_delay_rates = build_hourly_delay_rates(df)
    df = add_expected_delays(df, hourly_delay_rates)
    carrier_adjusted_delays = build_carrier_adjusted_delays(df)

    # Los resultados se redondean a 4 decimales
    hourly_delay_rates = hourly_delay_rates.round(4)
    carrier_adjusted_delays = carrier_adjusted_delays.round(4)

    save_table(hourly_delay_rates, "hourly_delay_rates.csv")
    save_table(carrier_adjusted_delays, "carrier_adjusted_delays.csv")

    return hourly_delay_rates, carrier_adjusted_delays
