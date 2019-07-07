import igraph
import win32com.client as com
import pandas as pd
import numpy as np
import itertools
from typing import Sequence, List, Tuple
from itertools import groupby
from math import ceil


def remove_loops(sequence: List[int]) -> List[int]:
    """
    This function takes in a list of numbers, finds any with duplicates, and all longest sequence between duplicates
    :param sequence:
    :return: list of numbers
    """
    # make list copy
    sequence = [item for item in sequence]

    item_set = set(sequence)
    if len(sequence) != len(item_set):
        for item in item_set:
            if sequence.count(item) > 1:
                last_index = sequence[::-1].index(item)
                first_index = sequence.index(item)
                del sequence[first_index + 1:last_index * -1]

    return sequence


class VissimRoadNet(igraph.Graph):
    """
    This class extends the igraph Graph object to allow connection with a VISSIM
    """
    VISSIM_Edge_Attributes = ['No', 'FromNode', 'ToNode', 'FromEdges', 'ToEdges', 'LinkSeq', 'Length', 'IsTurn', 'Type',
                              'Closed']

    def __init__(self, net=None, edge_ff='edge_free_flow.pkl.gz', *args, **kwargs):
        """
        Initializes the VissimRoadNet graph using a VISSIM network
        :param net: win32com.gen_py.[VISSIM COM GUID].INet

        VISSIM network object who's dynamic assignment graph will be read

        :param args:
        :param kwargs:

        Other arguments will be sent to constructor for parent igraph.Graph class.
        """
        super(VissimRoadNet, self).__init__(directed=True, *args, **kwargs)
        if type(net).__name__ == "INet":
            self.visedges = self.read_vissim_net(net)
            self.vissim_net_to_igraph()
            self.parking_lots = self.read_parking_lot(net)

            # set initial edge volume
            self.edge_volume = pd.Series(0, index=self.visedges.index, dtype=int)
            self.veh_paths = {}
            self.edge_ff = pd.read_pickle(edge_ff)
            self._traveltime = pd.Series(pd.np.nan, index=self.visedges.index, dtype=float)
            self._traveltime.loc[self.edge_ff.index] = self.edge_ff['TravelTime mean']
            empty_traveltime = self._traveltime.index[self._traveltime.isna()]
            self._traveltime.loc[empty_traveltime] = self.visedges.loc[empty_traveltime, 'Length'] / 51.3333  # ft/s
            self._traveltimeperiod = 1
            # or 35 mph

            # set initial weight value for path search
            self.es['weight'] = self._traveltime.to_list()

    def vissim_net_to_igraph(self):
        """
        This function takes in a VISSIM network COM object, then reads it and converts it to a VissimRoadNet object
        """

        all_edges = self.visedges

        # read each edge into graph, build vertices as we go
        for index in all_edges.index:
            if not all_edges.loc[index].OriginVertex:  # fresh edge that doesn't have origin vertices assigned
                # create and add origin vertex to graph
                vertex_name = 'visnode.' + str(all_edges.loc[index].FromNode) + '.' + str(index)
                self.add_vertex(name=vertex_name, node=all_edges.loc[index].FromNode)

                # add this edge's origin vertex as DestinVertex of all edges going into it
                vertex_enter_edges = all_edges.loc[index].FromEdges
                if vertex_enter_edges:
                    vertex_enter_edges = [int(ed) for ed in vertex_enter_edges.split(',')]
                    all_edges.loc[vertex_enter_edges, 'DestinVertex'] = vertex_name
                    # add the vertex to the OriginVertex of other edges going to the same edges
                    vertex_exit_edges = [ed.split(',') for ed in all_edges.loc[vertex_enter_edges].ToEdges]
                    vertex_exit_edges = [int(ed) for ed in itertools.chain.from_iterable(vertex_exit_edges) if ed]
                    all_edges.loc[vertex_exit_edges, 'OriginVertex'] = vertex_name
                else:  # add vertex only to this edge
                    all_edges.loc[index, 'OriginVertex'] = vertex_name

            if not all_edges.loc[index].DestinVertex:  # fresh edge that doesn't have destination vertices assigned
                # create and add destination vertex to graph
                vertex_name = 'visnode.' + str(all_edges.loc[index].ToNode) + '.' + str(index)
                self.add_vertex(name=vertex_name, node=all_edges.loc[index].ToNode)

                # add this edge's destination vertex as OriginVertex of all edges going from it
                vertex_exit_edges = all_edges.loc[index].ToEdges
                if vertex_exit_edges:
                    vertex_exit_edges = [int(ed) for ed in vertex_exit_edges.split(',')]
                    all_edges.loc[vertex_exit_edges, 'OriginVertex'] = vertex_name
                    # add the vertex to the DestinVertex of other edges coming from the same edges
                    vertex_enter_edges = [ed.split(',') for ed in all_edges.loc[vertex_exit_edges].FromEdges]
                    vertex_enter_edges = [int(ed) for ed in itertools.chain.from_iterable(vertex_enter_edges) if ed]
                    all_edges.loc[vertex_enter_edges, 'DestinVertex'] = vertex_name
                else:  # add vertex only to this edge
                    all_edges.loc[index, 'DestinVertex'] = vertex_name

            # add this edge to the graph
            # if not all_edges.loc[index, 'Closed']: # TODO apply closed status during edge cost analysis
            self.add_edge(all_edges.loc[index, 'OriginVertex'],
                          all_edges.loc[index, 'DestinVertex'],
                          name="visedge." + str(index))

        return all_edges

    @classmethod
    def read_vissim_net(cls, vissim_net) -> pd.DataFrame:
        # read edges into dataframe
        all_edges = pd.DataFrame(
            [list(row) for row in vissim_net.Edges.GetMultipleAttributes(cls.VISSIM_Edge_Attributes)],
            columns=cls.VISSIM_Edge_Attributes
        )
        # filter only open dynamic assignment edges
        all_edges = all_edges[all_edges.Type == 'DYNAMICASSIGNMENT']
        # properly type cast all the columns
        all_edges.No = all_edges.No.astype('int32')
        all_edges.FromNode = all_edges.FromNode.astype('int32')
        all_edges.ToNode = all_edges.ToNode.astype('int32')
        all_edges = all_edges.astype({
            'FromEdges': str,
            'ToEdges': str,
            'IsTurn': bool,
            'Type': 'category',
            'Closed': bool
        }, copy=False)
        all_edges['OriginVertex'] = ""
        all_edges['DestinVertex'] = ""
        # use edge numbers as index
        all_edges.set_index('No', inplace=True, verify_integrity=True, drop=True)
        return all_edges

    def read_parking_lot(self, vissim_net) -> pd.DataFrame:
        """
        This function takes in a VISSIM INet object and returns a table with the parkinglot association to
        nodes relationship
        :param vissim_net: VISSIM INet object
        :return: Dataframe with parking lot number, zone number, and node number
        """

        parking_lots = vissim_net.ParkingLots.GetMultipleAttributes(["No", "Zone", "Type"])
        parking_lots = pd.DataFrame([list(pk) for pk in parking_lots], columns=["No", "Zone", "Type"])
        parking_lots = parking_lots[parking_lots["Type"] == 'ZONECONNECTOR']
        parking_lots["Type"] = ""  # switch type to indicate whether the lot is origin or destination
        parking_lots = parking_lots.set_index('No')
        parking_lots["Zone"] = parking_lots["Zone"].astype(int)
        parking_lots["Node"] = 0
        parking_lots["VertexName"] = ''

        vissim_net.Paths.ReadDynAssignPathFile()
        paths = vissim_net.Paths.GetMultipleAttributes(['FromParkLot', 'ToParkLot', 'EdgeSeq'])
        paths = pd.DataFrame([list(p) for p in paths], columns=['FromParkLot', 'ToParkLot', 'EdgeSeq'])
        paths[['FromParkLot', 'ToParkLot']] = paths[['FromParkLot', 'ToParkLot']].astype(int, copy=False)

        # filter the path list to reduce run time
        from_lot_paths = paths.drop_duplicates(subset=['FromParkLot'])
        to_lot_paths = paths.drop_duplicates(subset=['ToParkLot'])
        for index, path in from_lot_paths.iterrows():
            first_edge = int(path.EdgeSeq.split(',')[0])
            first_node = self.visedges.loc[first_edge, 'FromNode']
            first_vertex = self.visedges.loc[first_edge, 'OriginVertex']
            # set origin lot node
            parking_lots.loc[path.FromParkLot, 'Node'] = first_node
            parking_lots.loc[path.FromParkLot, 'VertexName'] = first_vertex
            parking_lots.loc[path.FromParkLot, 'Type'] = 'origin'

        for index, path in to_lot_paths.iterrows():
            last_edge = int(path.EdgeSeq.split(',')[-1])
            last_node = self.visedges.loc[last_edge, 'ToNode']
            last_vertex = self.visedges.loc[last_edge, 'DestinVertex']
            # set destination lot node
            parking_lots.loc[path.ToParkLot, 'Node'] = last_node
            parking_lots.loc[path.ToParkLot, 'VertexName'] = last_vertex
            parking_lots.loc[path.ToParkLot, 'Type'] = 'destination'

        return parking_lots

    def parking_lot_routes(self,
                          origin_lot: (int, Sequence[int]),
                          destination_lot: (int, Sequence[int])) -> Tuple[list, list]:
        """
        This function computes the least costly path(s) between parking lot pair(s)
        :param origin_lot: The origin parking lot number as defined in VISSIM
        :param destination_lot: The destination parking lot number as defined in VISSIM
        :return: sequence of node numbers as a list
        """

        origin_vertex = self.parking_lots.loc[origin_lot, 'VertexName']
        destination_vertex = self.parking_lots.loc[destination_lot, 'VertexName']
        edge_ind_seqs = self.get_shortest_paths(v=origin_vertex,
                                                to=destination_vertex,
                                                weights='weight',
                                                output='epath')

        edge_seqs = [self.es[edge_seq] for edge_seq in edge_ind_seqs]

        node_seqs = [[self.vs[edge.target]['node'] for edge in edge_seq[:-1]] for edge_seq in edge_seqs]

        # remove consecutive duplicate nodes
        node_seqs = [[node[0] for node in groupby(node_seq)] for node_seq in node_seqs]

        edge_no_seqs = [self.visedges.index[edge_ind_seq] for edge_ind_seq in edge_ind_seqs]
        return node_seqs, edge_no_seqs

    def add_volume(self, edge_no_seq: Sequence[int]) -> None:
        """
        This function takes in a list of edge no sequence paths and add to their volume counts
        :param edge_no_seq:
        :return:
        """
        self.edge_volume.loc[edge_no_seq] = self.edge_volume.loc[edge_no_seq] + 1

    def remove_volume(self, edge_no_seq: Sequence[int]) -> None:
        """
        This function takes in a list of edge no sequence paths and removes from their volume counts
        :param edge_no_seq:
        :return:
        """
        self.edge_volume.loc[edge_no_seq] = self.edge_volume.loc[edge_no_seq] - 1
        self.edge_volume.clip_lower(0, inplace=True)

    def update_volume(self, vis_net):
        new_vehs = vis_net.Vehicles.GetDeparted().GetAll()
        for veh in new_vehs:
            new_path = [int(edge) for edge in veh.Path.AttValue('EdgeSeq').split(',')]
            self.veh_paths[veh.AttValue('No')] = new_path
            self.add_volume(new_path)

        departed_vehs = vis_net.Vehicles.GetArrived().GetAll()
        for veh in departed_vehs:
            old_path = self.veh_paths[veh.AttValue('No')]
            self.remove_volume(old_path)

    def update_weights(self, vis_net):
        current_DTA_period = ceil(vis_net.Simulation.SimulationSecond / vis_net.DynamicAssignment.AttValue('EvalInt'))
        # update recorded travel time
        if current_DTA_period > self._traveltimeperiod:
            new_travel_times = vis_net.Edges.GetMultiAttValues(f'TravTmRaw({current_DTA_period - 1})')
            # remove edges without recorded travel time
            new_travel_times = [edge for edge in new_travel_times if edge[1]]
            index, new_travel_times = tuple(zip(*new_travel_times))
            self._traveltime.loc[index] = list(new_travel_times)
            self._traveltimeperiod = current_DTA_period
            # increase travel time for closed edges
            closed_edges = self.visedges['Closed'].astype(bool)
            self._traveltime.loc[closed_edges] = 99999

            # TODO change weights to travel time plus marginal cost instead of just travel time
            self.es['weight'] = self._traveltime.to_list()


# Testing code
if __name__ == "__main__":
    Vissim = com.gencache.EnsureDispatch("Vissim.Vissim")
    from win32com.client import constants as c

    FileName = r"C:\Users\ITSLab\Documents\Oliver Liang\Urban Freeway Dyn Assign Redmond.US\Vol150per\Vol150per.inpx"
    # FileName = r"E:\Thesis\Inital test network"
    Vissim.LoadNet(FileName)
    Net = Vissim.Net
    if not Net.DynamicAssignment.CreateGraph(c.CGEdgeTypeDynamicAssignment):
        print("VISSIM Network Graph Creation error")
        exit(1)

    road_graph = VissimRoadNet(Net)
    # road_graph.write_svg(r"J:\Thesis\test.svg", width=3000, height=3000)
    Vissim.Exit()
    com.dynamic.