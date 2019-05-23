from io import TextIOWrapper
from typing import Mapping, Sequence, List, Dict
import pandas as pd

COLUMNTYPE = {'NO': int, 'TRAVTM': float, 'VOL': int, 'FROMNODE': int,
              'TONODE': int, 'CURITERIDX': int, 'NUMCONVSIMRUNS': int, 'EVALINT': int}


def colu_to_type(name: str):
    """
    This function returns the correct data type for given dynamic assignment column names

    :param name: str of field name
    :return: int, float, or str class types
    """
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


def timevol_table(frame: pd.DataFrame) -> pd.DataFrame:
    """
    This function takes a dynamic assignment time volume table in the format described here:

    https://cgi.ptvgroup.com/vision-help/VISSIM_11_ENG/#16_DateienUebersicht/Dateien_Dyn_Uml.htm

    and converts it to the following:

    NO | VehType | Period | TRAVTMNEW | VOLNEW

    :param frame: the dataframe from dynamic_assignment_file_read to be transformed
    :param interval: the dynamic assignment interval length used in the simulation
    :return: dataframe of transformed data
    """

    def pick_no_and_cols_melt(data, col_name_start):
        # pick out relevant columns by names
        columns = list(frame.columns.values)
        columns = [col for col in columns if col.startswith(col_name_start)]
        data: pd.DataFrame = data[['NO'] + columns]
        # replace word in column name so only period and vehicle type is contained
        columns = dict(zip(columns, [col.split('(')[-1].strip(')') for col in columns]))
        data = data.rename(index=str, columns=columns)
        # melt the data frame along the value columns
        data = data.melt(id_vars=['NO'], var_name='TEMP', value_name=col_name_start)
        # Split the temp column
        new_columns = data['TEMP'].str.split(',', n=1, expand=True)
        data.drop(columns=['TEMP'], inplace=True)
        data['Period'] = new_columns[0].astype(int)
        data['VehType'] = new_columns[1]
        data.sort_values(by=['NO', 'VehType', 'Period'], inplace=True)
        return data

    out_frame = pick_no_and_cols_melt(frame, 'TRAVTMNEW')
    out_frame['VOLNEW'] = pick_no_and_cols_melt(frame, 'VOLNEW')['VOLNEW']
    out_frame = out_frame[['NO', 'VehType', 'Period', 'TRAVTMNEW', 'VOLNEW']]
    return out_frame


def dynamic_assignment_file_read(file: [str, TextIOWrapper]) -> Dict[str, pd.DataFrame]:
    """
    This function reads a VISSIM dynamic assignment file with extension bew or weg and converts all the contained tables
    to dataframes

    :param file: either a str path to the file or a file wrapper it self.
    :return: a dictionary of dataframes referenced by their table content from VISSIM file
    """

    if type(file) is str:
        fileIO: TextIOWrapper = open(file, 'r')
    else:
        fileIO: TextIOWrapper = file

    tablenames = ["DynAsnAttr", "EdgeAttr", "VolTime"]
    output_dict: Dict[str, pd.DataFrame] = {}
    current_table: str = ""
    attributes: Sequence[str] = []

    for line in fileIO.readlines():
        # add tablename
        if line[:8] == "* Table:":
            current_table = tablenames[0]
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
