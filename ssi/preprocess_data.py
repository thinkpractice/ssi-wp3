from typing import List
from .data_logging import DataLogger
import pandas as pd
import os
import tqdm


def split_coicop(coicop_column: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({"coicop_number": coicop_column,
                         "coicop_division": coicop_column.str[:2],
                         "coicop_group": coicop_column.str[:3],
                         "coicop_class": coicop_column.str[:4],
                         "coicop_subclass": coicop_column.str[:5],
                         "coicop_subsubclass": coicop_column,
                         })


def get_category_counts(dataframe: pd.DataFrame, coicop_column: str, product_id_column: str) -> pd.DataFrame:
    unique_coicop = pd.Series(
        dataframe[dataframe[coicop_column].str.len() == 6][coicop_column].unique())
    split_coicop_df = split_coicop(unique_coicop)

    coicop_counts = dataframe.groupby(by=[coicop_column])[product_id_column].nunique(
    ).reset_index().rename(columns={product_id_column: "count"})
    return split_coicop_df.merge(coicop_counts, on=coicop_column)


def add_leading_zero(dataframe: pd.DataFrame, coicop_column: str = "coicop_number") -> pd.DataFrame:
    shorter_columns = dataframe[coicop_column].str.len() == 5
    dataframe.loc[shorter_columns, coicop_column] = dataframe[shorter_columns][coicop_column].apply(
        lambda s: f"0{s}")
    return dataframe


def add_unique_product_id(dataframe: pd.DataFrame, product_description_column: str = "ean_name") -> pd.DataFrame:
    dataframe["product_id"] = dataframe[product_description_column].str.apply(
        hash)
    return dataframe


def preprocess_data(dataframe: pd.DataFrame, coicop_column: str = "coicop_number", product_id_column: str = "ean_number") -> pd.DataFrame:
    split_coicop_df = get_category_counts(
        dataframe, coicop_column=coicop_column, product_id_column=product_id_column)
    dataframe = dataframe.merge(
        split_coicop_df, on=coicop_column, suffixes=['', '_y'])
    dataframe = add_leading_zero(dataframe, coicop_column=coicop_column)
    dataframe = add_unique_product_id(dataframe)
    return dataframe


def combine_revenue_files(revenue_files: List[str], sort_columns: List[str], sort_order: List[bool], engine: str = "pyarrow") -> pd.DataFrame:
    combined_dataframe = pd.concat([pd.read_parquet(revenue_file, engine=engine)
                                    for revenue_file in tqdm.tqdm(revenue_files)])
    combined_dataframe = combined_dataframe.sort_values(
        by=sort_columns, ascending=sort_order).reset_index(drop=True)
    return combined_dataframe


def combine_revenue_files_in_folder(data_directory: str, supermarket_name: str, sort_columns: List[str], sort_order: List[bool], filename_prefix: str = "Omzet") -> pd.DataFrame:
    revenue_files = [os.path.join(data_directory, filename) for filename in os.listdir(
        data_directory) if filename.startswith(filename_prefix) and supermarket_name in filename]
    return combine_revenue_files(revenue_files, sort_columns=sort_columns, sort_order=sort_order)


def save_combined_revenue_files(data_directory: str, output_filename: str, supermarket_name: str, log_directory: str, filename_prefix: str = "Omzet", engine: str = "pyarrow"):
    data_logger = DataLogger(log_directory)

    combined_df = combine_revenue_files_in_folder(
        data_directory, supermarket_name, filename_prefix, sort_columns=["bg_number", "month", "coicop_number"], sort_order=[True, True, True])
    data_logger.log_before_preprocessing(combined_df, "coicop_number")

    combined_df = preprocess_data(combined_df)

    # data_logger.log_after_preprocessing(combined_df, "coicop_number", )

    combined_df.to_parquet(os.path.join(
        data_directory, output_filename), engine=engine)