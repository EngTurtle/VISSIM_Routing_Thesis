from typing import Sequence
from os import path, walk, getenv
import pathos.multiprocessing as mp
from DynFileFuncs import dynamic_assignment_file_read, timevol_table
import pandas as pd

ONEDRIVEPATH = getenv('OneDriveConsumer', default=r"C:\Users\ITSLab")


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


def functions_expansion(*args):
    def map_func(item):
        for func in args:
            item = func(item)
        return item
    return map_func


# gather list of route files
if __name__ == "__main__":
    files = files_by_ext(path.join(ONEDRIVEPATH, r"Documents\University Documents\Thesis\Urban Freeway Dyn Assign Redmond.US"),
                 'bew')

    with mp.Pool() as pool:
        tables = pool.map(functions_expansion(dynamic_assignment_file_read,
                                              lambda tbd: tbd['VolTime'],
                                              timevol_table
                                              ), files)
    sim_itr = [int(path.basename(fr).split('.')[0].split('_')[-1]) for fr in files]
    for itr, table in zip(sim_itr, tables):
        table['ITR'] = itr

    end_table = pd.concat(tables)
