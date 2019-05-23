from io import TextIOWrapper
from typing import Mapping, Sequence
import pandas as pd

TABLENAMES = {'bew': ["DynAsnAttr", "EdgeAttr", "EdgeVolTime"],
              'weg': ["DynAsnAttr", "EdgeAttr", "PathVolTime"]}

COLUMNTYPE = {'NO': int, 'TRAVTM': float, 'VOL': int, 'FROMNODE': int,
              'TONODE': int, 'CURITERIDX': int, 'NUMCONVSIMRUNS': int, 'EVALINT': int}


def colu_to_type(name: str):
    for col in COLUMNTYPE.keys():
        if name.startswith(col):
            return COLUMNTYPE[col]
    return str


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

    # cast each column to the correct type
    for frame in output_dict.values():
        for col in frame.columns.values:
            frame[col] = frame[col].astype(colu_to_type(col))

    if type(file) is str:
        fileIO.close()

    return output_dict

if __name__ == "__main__":
    file = r"C:\Users\ollie\OneDrive\Documents\University Documents\Thesis\Urban Freeway Dyn Assign Redmond.US\Sim 3\ref_tsm.bew"
    tables = dynamic_assignment_file_read(file)