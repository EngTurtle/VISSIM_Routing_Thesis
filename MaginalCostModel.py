import pandas as pd
import numpy as np
from collections import OrderedDict


class EdgeModel:
    """
    This class will provide fitting and be a callable object to estimate marginal cost
    """

    def __init__(self, data: [pd.DataFrame, None] = None):
        """7
        Class init method,
        :param data:
        """
        if data:
            # Run model fitting algorithm

            pass


class NetworkModel:
    """
    This model fits and computes the travel time and marginal travel time for all edges in a dynamic assignment graph
    for vissim
    """

    def __init__(self, vis_edges: pd.DataFrame):
        self.edges = vis_edges

        # generate dictionary to store the models
        models = [None] * vis_edges.shape[0]
        models = zip(vis_edges.index, models)
        self.models = OrderedDict(models)
