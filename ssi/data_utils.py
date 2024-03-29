import pandas as pd
import os


def export_dataframe(dataframe: pd.DataFrame, path: str, filename: str, index: bool = False, delimiter: str = ";"):
    csv_directory = os.path.join(path, "csv")

    if not os.path.exists(csv_directory):
        print(f"Creating log directory {csv_directory}")
        os.makedirs(csv_directory, exist_ok=True)

    html_directory = os.path.join(path, "html")
    if not os.path.exists(html_directory):
        print(f"Creating log directory {html_directory}")
        os.makedirs(html_directory, exist_ok=True)

    dataframe.to_csv(os.path.join(
        csv_directory, filename + ".csv"), sep=delimiter, index=index)

    if isinstance(dataframe, pd.Series):
        dataframe = pd.DataFrame(dataframe)

    dataframe.to_html(os.path.join(html_directory, filename + ".html"))


def year_month_to_date(dataframe: pd.DataFrame, year_month_column: str) -> pd.DataFrame:
    dataframe[year_month_column] = pd.to_datetime(
        dataframe[year_month_column], format="%Y-%m")
    return dataframe
