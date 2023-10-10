from dotenv import load_dotenv
from typing import Dict, Any, Optional
import argparse
import pandas as pd
import os
import tqdm

def get_column_types(filename: str) -> Optional[Dict[str, Any]]:
    # From Justin's code
    if filename.startswith("omzeteans"):
        return {'BgNr': str, 'Maand': str, 'CoicopNr': str, 'CoicopNaam': str, 'IsbaNr': str,
                'IsbaNaam': str, 'EsbaNr': str, 'EsbaNaam': str, 'Rep_id': str,
                    'EanNr': str, 'EanNaam': str, 'Omzet': np.float32, 'Aantal': np.float32}
    elif filename.lower().startswith("output"):
        return {'BgNr': str, 'BgNaam':str, 'CoicopNr':str, 'CoicopNaam':str, 'IsbaNr':str, 'IsbaNaam':str, 'EsbaNr':str, 'EsbaNaam':str, 'Rep_id':str, 'EanNr': str, 'EanNaam':str } 
    return None

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input-directory",
                    help="The directory to read the csv files from")
parser.add_argument("-o", "--output-directory", default=None,
                    help="The directory to read the parquet files to")
parser.add_argument("-d", "--delimiter", default=";",
                    help="The delimiter used in the csv files")
parser.add_argument("-ec", "--encoding", default="utf-8",
                    help="The encoding of the csv files (default: utf-8)")
parser.add_argument("-e", "--extension", default=".csv",
                    help="The extension for the csv files")
parser.add_argument("-de", "--decimal", default=",",
                    help="The decimal separator used in the csv files")
args = parser.parse_args()

load_dotenv()

input_directory = os.getenv(
    "INPUT_DIRECTORY") if not args.input_directory else args.input_directory

# If no output directory is specified, try to get output directory from env
# If no output directory is specified in env, use input directory.
output_directory = os.getenv(
    "OUTPUT_DIRECTORY") if not args.output_directory else args.output_directory
output_directory = input_directory if not output_directory else output_directory

input_filenames = [os.path.join(input_directory, filename)
                   for filename in os.listdir(input_directory)
                   if filename.endswith(args.extension)]

print(
    f"Reading all {args.extension} files from {input_directory} and writing them to {output_directory}")
progress_bar = tqdm.tqdm(input_filenames)

# The CPI csv files have no header, so we need to set header=None
# also the number of columns varies per line. Pandas only handles this
# if we can specify the column names up front
# TODO change for real columns later
# column_names = [str(i) for i in range(0, 13)]

for input_filename in progress_bar:
    filename = os.path.basename(input_filename).replace(args.extension, "")
    output_filename = os.path.join(output_directory, f"{filename}.parquet")
    progress_bar.set_description(
        f"Writing {input_filename} to {output_filename}")

    first_line = pd.read_csv(input_filename, sep=args.delimiter, nrows=1)
    
    header_names = None if filename.lower().startswith("kassa") else [f"column_{i}" for i in range(0, len(first_line.columns))]

    # C engine is the only one that can read the CPI files
    df = pd.read_csv(input_filename, sep=args.delimiter,
                     engine="pyarrow", encoding=args.encoding, decimal=args.decimal, names=header_names)
    df.to_parquet(output_filename, engine="pyarrow")
