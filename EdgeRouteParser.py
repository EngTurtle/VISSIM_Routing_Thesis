from io import TextIOWrapper
from typing import Mapping, Sequence
from os import path, walk, getenv
import pandas as pd
import ntpath
import multiprocessing as mp

TABLENAMES = {'bew': ["DynAsnAttr", "EdgeAttr", "EdgeVolTime"],
              'weg': ["DynAsnAttr", "EdgeAttr", "PathVolTime"]}

ONEDRIVEPATH = getenv('OneDriveConsumer', default=r"C:\Users\ITSLab")


def tonumeric(instr: str) -> [int, float, str]:
    """
    This function tries to convert a string to a integer first, then tries float, and returns string if all fails
    if empty string, it return none
    :param instr: input string
    :return: either int, float, or original string
    """
    if instr == '':
        return None

    try:
        return int(instr)
    except ValueError:
        try:
            return float(instr)
        except ValueError:
            return instr


def dynamic_assignment_file_read(file: [str, TextIOWrapper]) -> Mapping[str, pd.DataFrame]:
    """
    This function reads a VISSIM dynamic assignment file with extension bew or weg and converts all the contained tables
    to dataframes
    :param file: either a str path to the file or a file wrapper it self.
    :return: a dictionary of dataframes referenced by their table content from VISSIM file
    """
    fileIO: TextIOWrapper
    if type(file) is str:
        fileIO = open(file, 'r')
    else:
        fileIO = file

    tablenames = TABLENAMES[fileIO.name.split('.')[-1]]
    output_dict: Mapping[str, pd.DataFrame] = {}
    current_table: str = ""
    attributes: Sequence[str] = []

    for line in fileIO.readlines():
        # add tablename
        if line[:8] == "* Table:":
            current_table = tablenames[0]
            if current_table not in output_dict:
                current_table = current_table + '.0'
            else:
                current_table = current_table.split('.')[0] + '.' + str(int(current_table.split('.')[1]) + 1)
            if len(tablenames) > 1:
                tablenames = tablenames[1:]

        # create table dataframe
        elif line[0] == '$' and current_table:
            if current_table not in output_dict:
                attributes = line.strip().strip('\n').split(':')[1].split(';')
                output_dict[current_table] = pd.DataFrame(columns=attributes)

        # append datarow to dataframe
        split_line = line.strip().strip('\n').split(';')
        if str.isdigit(split_line[0]) and current_table in output_dict:
            split_line = [tonumeric(value) for value in split_line]
            output_dict[current_table] = output_dict[current_table] \
                .append(dict(zip(attributes, split_line)), ignore_index=True)

    if type(file) is str:
        fileIO.close()

    return output_dict


def files_by_ext(parent_dir: str, ext: str) -> Sequence[str]:
    """
    This function finds all files with the provided extension under the provided parent_dir
    :param parent_dir: a folder string path to search
    :param ext: a file extension
    :return: a list of full string paths
    """
    parent_dir = parent_dir.strip('"').strip("'")
    if not path.isdir(parent_dir):
        raise ValueError("\"{}\" is not a valid directory".format(parent_dir))

    ext = ext.split('.')[-1]
    if not ext:
        raise ValueError(ext + " is not a valid extension to search")

    file_paths = []
    for root, directories, files in walk(parent_dir):
        for file in files:
            if file.endswith('.' + ext):
                file_paths.append(path.join(root, file))

    return file_paths


def read_tables_mp(files: Sequence[str]):
    with mp.Pool() as pool:
        return pool.map(dynamic_assignment_file_read, files)


# gather list of route files
if __name__ == "__main__":
    files = files_by_ext(path.join(ONEDRIVEPATH, r"Documents\University Documents\Thesis\Urban Freeway Dyn Assign Redmond.US"),
                 'bew')

    tables = read_tables_mp(files)
