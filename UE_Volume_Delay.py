#!/usr/bin/env python
# coding: utf-8

# # Initial Volume Delay Data Collection
# 
# This file will run the network under varying levels of traffic load in order to gather network performance for calibrating traffic assignment models.


from os import makedirs, remove
# Neede Libraries
from os.path import abspath, exists
from os.path import join as ptjoin
from os.path import split as ptsplit
from shutil import copyfile

# parallel processing
import ipyparallel as ipp
import numpy as np
# COM-Server
import win32com.client as com
from win32com.client import constants as c

from EdgeRouteParser import files_by_ext

ipclient = ipp.Client()

# Start VISSIM
Vissim = com.gencache.EnsureDispatch("Vissim.Vissim")


# Function to create folder if it doesn't exist


def ensure_folder(pathstr: str):
    if not exists(pathstr):
        makedirs(pathstr)


# Setting the parameters used for simulation


Network_File = abspath(
    r"C:\Users\Public\Documents\PTV Vision\PTV Vissim 9\Examples Demo\Urban Freeway Dyn Assign Redmond.US\I405 OD.inpx"
)

DTA_Parameters = dict(
    # DTA Parameters
    EvalInt=600,  # seconds
    ScaleTotVol=False,
    ScaleTotVolPerc=1,
    CostFile='costs.bew',
    ChkEdgOnReadingCostFile=True,
    PathFile='paths.weg',
    ChkEdgOnReadingPathFile=True,
    CreateArchiveFiles=True,
    VehClasses='',

    # Path cost parameters
    CostCalcInt=c.DynAssignCostCalculationIntervalPreviousSimRun,
                # DynAssignCostCalculationIntervalCurrentSimRun
                # DynAssignCostCalculationIntervalPreviousSimRun
    TravTmCalcMethod=c.DynAssignTraveltimeCalculationMethodEdgeTraveltimes,
                     # DynAssignTraveltimeCalculationMethodEdgeTraveltimes
                     # DynAssignTraveltimeCalculationMethodPathTraveltimes
    Smoothing=c.SmoothingMethodExpSmoothing,
              # SmoothingMethodExpSmoothing
              # SmoothingMethodMethodOfSuccessiveAverages
    ExpSmoothingFact=0.2,

    # Path search parameters
    SearchNewPaths=True,
    SearchAltPaths=True,
    PathSelType=c.DynAssignPathSelectionTypeDecideAtStartOnly,
                # DynAssignPathSelectionTypeDecideAtStartOnly
                # DynAssignPathSelectionTypeDecideRepeatedly

    # Path selection parameters
    AvoidDetours=True,
    AvoidDetoursFact=2.5,
    PathsRejectHighCost=True,
    PathsRejectCostPerc=0.75,
    PathsLimitNumPaths=False,
    PathsLimitMaxNumPaths=999,
    PathSelMethod=c.DynAssignPathSelectionMethodStochasticKirchhoff,
                  # DynAssignPathSelectionMethodEquilibrium
                  # DynAssignPathSelectionMethodStochasticKirchhoff
                  # DynAssignPathSelectionMethodUseVolumeOld
    KirchExp=3.5,
    CorrectOverlappingPaths=True,

    # Convergence
    ConvgBehav=c.ConvergenceBehaviorTypeCompleteMultiRun
)

# Simulation parameters
Sim_Parameters = dict(
    SimPeriod=4500,
    StartTm=0.0,

    SimRes=5,
    RandSeed=468,  # random.randint(1,10000),
    VolumeIncrDynAssign=0.,

    NumRuns=20,
    RandSeedIncr=0,

    UseMaxSimSpeed=True,
    RetroSync=False,

    SimBreakAt=0,
    NumCores=5,
)


# Define functions to convert to and from VISSIM Demand Matrix


# for VISSIM matrix, the row number denotes the origin, the column number denotes the destination

def IMatrix_to_numpy(matrix):
    assert type(matrix).__name__ == 'IMatrix'
    rows = matrix.RowCount
    columns = matrix.ColCount

    out = np.zeros((rows, columns), dtype=float)
    for row in range(rows):
        for col in range(columns):
            out[row, col] = int(matrix.GetValue(row + 1, col + 1))

    return out


def set_IMatrix_from_numpy(matrix, np_matrix: np.ndarray):
    assert type(matrix).__name__ == 'IMatrix'
    assert matrix.RowCount == np_matrix.shape[0]
    assert matrix.ColCount == np_matrix.shape[1]
    np_matrix = np.around(np_matrix, 0).astype(int)
    rows = matrix.RowCount
    columns = matrix.ColCount
    for row in range(rows):
        for col in range(columns):
            matrix.SetValue(row + 1, col + 1, np_matrix[row, col])


# We start by opening the network to be tested and adjust its settings


Vissim.SuspendUpdateGUI()
Vissim.LoadNet(Network_File)

DynamicAssignment = Vissim.Net.DynamicAssignment
for attname, attvalue in DTA_Parameters.items():
    DynamicAssignment.SetAttValue(attname, attvalue)

Simulation = Vissim.Net.Simulation
for attname, attvalue in Sim_Parameters.items():
    Simulation.SetAttValue(attname, attvalue)

Vissim.ResumeUpdateGUI()

# Gather all dynamic assignment demand matrices and zone numbers


demand_matrices = [IMatrix_to_numpy(dm.Matrix) for dm in DynamicAssignment.DynAssignDemands.GetAll()]
zones_NOs = [zn[1] for zn in Vissim.Net.Zones.GetMultiAttValues('No')]

# Implementing different simulation scenarios
# 
# Iterating from 10% to 150% traffic volume in 15 separate simulation runs.
# Each simulation run with 20 iterations at same traffic levels.


working_folder = abspath(r"../Urban Freeway Dyn Assign Redmond.US")

# create dictionary of sim working folder names and assiciated OD demand matricies
Volumes = {}
for multiple in np.arange(0.1, 1.6, 0.1):
    Volumes["Vol{:}per".format(int(multiple * 100))] = [np.around(dm * multiple, 0) for dm in demand_matrices]

signal_files = files_by_ext(Vissim.AttValue('WorkingFolder'), '.sig')

# set OD demand matricies and save as to working folder
Vissim.SuspendUpdateGUI()
for volname in Volumes.keys():

    # Set OD matrix
    for index, demand in enumerate(DynamicAssignment.DynAssignDemands.GetAll()):
        set_IMatrix_from_numpy(demand.Matrix, Volumes[volname][index])

    # Save file to folder
    sim_folder = ptjoin(working_folder, volname)
    ensure_folder(sim_folder)
    file_name = ptjoin(sim_folder, volname + ".inpx")
    Vissim.SaveNetAs(file_name)

    # Copy signal controller files
    for sig_file in signal_files:
        copyfile(sig_file, ptjoin(sim_folder, ptsplit(sig_file)[-1]))

    Volumes[volname] = file_name

Vissim.ResumeUpdateGUI()


# Define function to open each sim file saved from above and run the simulation
def run_VISSIM_file(filepath: str, clear_costs=False):
    import win32com.client as com2
    from os.path import abspath
    from os.path import join as ptjoin
    from os.path import split as ptsplit

    if clear_costs:
        working_folder = ptjoin(*list(ptsplit(abspath(filepath)))[:-1])
        weg_files = files_by_ext(working_folder, '.weg')
        bew_files = files_by_ext(working_folder, '.bew')
        for file in weg_files + bew_files:
            remove(file)

    # start new VISSIM instance and load file then run network
    print("Starting VISSIM for " + ptsplit(abspath(filepath))[-1])
    VissimInst = com2.gencache.EnsureDispatch("Vissim.Vissim")
    VissimInst.SuspendUpdateGUI()
    VissimInst.LoadNet(filepath)
    VissimInst.Graphics.CurrentNetworkWindow.SetAttValue("QuickMode", 1)
    VissimInst.Simulation.RunContinuous()
    VissimInst.ResumeUpdateGUI()
    VissimInst.Exit()
    print("Finished sim for " + ptsplit(abspath(filepath))[-1])


Vissim.Exit()

# Run the simulations in parallel using ipyparallel


instances = ipclient[:]
results = instances.map(run_VISSIM_file, Volumes.values())
