from luigi.contrib.external_program import ExternalProgramTask
from .parquet import convert_to_parquet
from .files import get_revenue_files_in_folder
from .preprocess_data import preprocess_data
import pandas as pd
import pathlib
import luigi
import os


class CleanCPIFile(ExternalProgramTask):
    """ This task converts CBS CPI CSV files to CSV file format that can be read by python.

    The CBS CPI files use an unusual encoding. The shell script takes an input 
    file, reads the input_filename, skips the first 3 bytes (BOM), and converts 
    them from cp1252 to utf-8. Last, it filters out the carriage returns '\r' 
    and writes the result to a file with output_filename.

    Parameters
    ----------
    input_filename : luigi.PathParameter
        The input filename of the original CBS CPI file.

    output_filename : luigi.PathParameter
        The output filename for the cleaned CBS CPI file.

    """
    input_filename = luigi.PathParameter()
    output_filename = luigi.PathParameter()

    def program_args(self):
        current_file_path = pathlib.Path(__file__).parent.resolve()
        return ['bash', os.path.join(current_file_path,  'convert_cpi_file.sh'), self.input_filename, self.output_filename]

    def output(self):
        """

        TODO: check if this doesn't cause the atomic writes problem mentioned here: 
        https://luigi.readthedocs.io/en/latest/luigi_patterns.html#atomic-writes-problem
        """
        return luigi.LocalTarget(self.output_filename)


class ConvertCSVToParquet(luigi.Task):
    """ This task converts a CSV file to a parquet file.

    Parameters
    ----------
    input_filename : luigi.PathParameter
        The input filename of the original CSV file.

    output_filename : luigi.PathParameter
        The output filename for the parquet file.

    delimiter : luigi.Parameter
        The delimiter used in the CSV file.

    """
    input_filename = luigi.PathParameter()
    output_directory = luigi.PathParameter(default="parquet_files")
    delimiter = luigi.Parameter(default=';')
    encoding = luigi.Parameter(default='utf-8')
    extension = luigi.Parameter(default='.csv')
    decimal = luigi.Parameter(default=',')

    def get_parquet_filename(self):
        return os.path.join(self.output_directory, os.path.basename(
            self.input_filename).replace(self.extension, ".parquet"))

    def requires(self):
        return CleanCPIFile(input_filename=self.input_filename, output_filename=self.get_parquet_filename())

    def run(self):
        with self.input().open('r') as input_file:
            with self.output().open('w') as output_file:
                convert_to_parquet(self.input_filename,
                                   input_file,
                                   output_file,
                                   delimiter=self.delimiter,
                                   encoding=self.encoding,
                                   extension=self.extension,
                                   decimal=',')

    def output(self):
        return luigi.LocalTarget(self.get_parquet_filename(), format=luigi.format.Nop)


class CombineRevenueFiles(luigi.Task):
    """ This task combines revenue files that were prepared by ConvertCSVToParquet into a single parquet file.

    Parameters
    ----------
    input_directory : luigi.Parameter
        The directory where the revenue files are stored.

    output_filename : luigi.Parameter
        The output filename for the combined revenue file.

    """
    input_directory = luigi.Parameter()
    output_filename = luigi.Parameter()
    store_name = luigi.Parameter()
    filename_prefix = luigi.Parameter(default="Omzet")
    parquet_engine = luigi.Parameter(default="pyarrow")
    sort_order = luigi.DictParameter(
        default={"bg_number": True, "month": True, "coicop_number": True})

    def requires(self):
        revenue_files = get_revenue_files_in_folder(
            self.input_directory,
            self.store_name,
            self.filename_prefix,
            ".csv")
        return [ConvertCSVToParquet(input_filename)
                for input_filename in revenue_files
                ]

    def output(self):
        return luigi.LocalTarget(self.output_filename, format=luigi.format.Nop)

    def run(self):
        combined_dataframe = None
        for input in self.input():
            with input.open("r") as input_file:
                revenue_file = pd.read_parquet(
                    input_file, engine=self.parquet_engine)
                if combined_dataframe is None:
                    combined_dataframe = revenue_file
                else:
                    combined_dataframe = pd.concat(
                        [combined_dataframe, revenue_file])

        combined_dataframe = combined_dataframe.sort_values(
            by=list(self.sort_order.keys()), ascending=list(self.sort_order.values())).reset_index(drop=True)

        with self.output().open('w') as output_file:
            combined_dataframe.to_parquet(
                output_file, engine=self.parquet_engine)


class PreprocessCombinedFile(luigi.Task):
    """ This task preprocesses the combined revenue file.

    Parameters
    ----------
    input_filename : luigi.Parameter
        The input filename of the combined revenue file.

    output_filename : luigi.Parameter
        The output filename for the preprocessed combined revenue file.

    coicop_column : luigi.Parameter
        The name of the column containing the coicop numbers.

    product_id_column : luigi.Parameter
        The name of the column containing the product ids.

    product_description_column : luigi.Parameter
        The name of the column containing the product descriptions.

    selected_columns : luigi.ListParameter
        Names of the columns to select.

    coicop_level_columns : luigi.ListParameter
        Names of the columns containing the coicop levels.

    column_mapping : luigi.DictParameter
        A dictionary containing the mapping of column names.

    """
    input_filename = luigi.Parameter()
    output_filename = luigi.Parameter()
    coicop_column = luigi.Parameter(default="coicop_number")
    product_id_column = luigi.Parameter(default="product_id")
    product_description_column = luigi.Parameter(default="ean_name")
    selected_columns = luigi.ListParameter(default=[])
    coicop_level_columns = luigi.ListParameter(default=[])
    column_mapping = luigi.DictParameter(default={})
    parquet_engine = luigi.Parameter(default="pyarrow")

    def requires(self):
        # TODO: check input_directory is derived wrongly, unless the combined file is in the same directory as the separate revenue files
        return CombineRevenueFiles(input_directory=os.path.dirname(self.input_filename),
                                   output_filename=self.input_filename.replace(
                                       ".parquet", "_preprocessed.parquet"),
                                   store_name=self.store_name,
                                   filename_prefix=self.filename_prefix,
                                   parquet_engine=self.parquet_engine,
                                   sort_order=self.sort_order)

    def run(self):
        with self.input().open("r") as input_file:
            combined_df = pd.read_parquet(
                input_file, engine=self.parquet_engine)

        combined_df = preprocess_data(
            combined_df,
            columns=self.selected_columns,
            coicop_column=self.coicop_column,
            product_id_column=self.product_id_column,
            product_description_column=self.product_description_column,
            column_mapping=self.column_mapping
        )

        with self.output().open('w') as output_file:
            combined_df.to_parquet(output_file, engine=self.parquet_engine)

    def output(self):
        return luigi.LocalTarget(self.output_filename, format=luigi.format.Nop)
