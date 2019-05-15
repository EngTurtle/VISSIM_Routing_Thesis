import igraph
import win32com.client as com
import pandas as pd
import itertools


class VissimRoadNet(igraph.Graph):
    """
    This class extends the igraph Graph object to allow connection with a VISSIM
    """
    VISSIM_Edge_Attributes = ['No', 'FromNode', 'ToNode', 'FromEdges', 'ToEdges', 'IsTurn', 'Type', 'Closed']

    def __init__(self, net, *args, **kwargs):
        """
        Initializes the VissimRoadNet graph using a VISSIM network
        :param net:
        :param args:
        :param kwargs:
        """
        super(VissimRoadNet, self).__init__(directed=True, *args, **kwargs)
        assert type(net).__name__ == "INet"
        self.net = net
        self.visedges = self.vissim_net_to_igraph(self.net)

    def vissim_net_to_igraph(self, vissim_net):
        """
        This function takes in a VISSIM network COM object, then reads it and converts it to a VissimRoadNet object
        :param vissim_net: win32com.gen_py.[VISSIM COM GUID].INet
        :return:
        """

        # read edges into dataframe
        all_edges = pd.DataFrame(
            [list(row) for row in vissim_net.Edges.GetMultipleAttributes(self.VISSIM_Edge_Attributes)],
            columns=self.VISSIM_Edge_Attributes
        )
        # filter only open dynamic assignment edges
        all_edges = all_edges[all_edges.Type == 'DYNAMICASSIGNMENT']
        # properly type cast all the columns
        all_edges.No = all_edges.No.astype('int32')
        all_edges.FromNode = all_edges.FromNode.astype('int32')
        all_edges.ToNode = all_edges.ToNode.astype('int32')
        all_edges.astype({
            'FromEdges': str,
            'ToEdges': str,
            'IsTurn': bool,
            'Type': 'category',
            'Closed': bool
        }, copy=False)
        all_edges['OriginVertex'] = ""
        all_edges['DestinVertex'] = ""
        # use edge numbers as index
        all_edges.set_index('No', inplace=True, verify_integrity=True, drop=False)

        # read each edge into graph, build vertices as we go
        for index in all_edges.index:
            if not all_edges.loc[index].OriginVertex:  # fresh edge that doesn't have origin vertices assigned
                # create and add origin vertex to graph
                vertex_name = 'visnode.' + str(all_edges.loc[index].FromNode) + '.' + str(index)
                self.add_vertex(name=vertex_name)

                # add this edge's origin vertex as DestinVertex of all edges going into it
                vertex_enter_edges = all_edges.loc[index].FromEdges
                if vertex_enter_edges:
                    vertex_enter_edges = [int(ed) for ed in vertex_enter_edges.split(',')]
                    all_edges.loc[vertex_enter_edges, 'DestinVertex'] = vertex_name
                    # add the vertex to the OriginVertex of other edges going to the same edges
                    vertex_exit_edges = [ed.split(',') for ed in all_edges.loc[vertex_enter_edges].ToEdges]
                    vertex_exit_edges = [int(ed) for ed in itertools.chain.from_iterable(vertex_exit_edges)]
                    all_edges.loc[vertex_exit_edges, 'OriginVertex'] = vertex_name
                else:  # add vertex to all edges going directly to and from node
                    from_node = all_edges.loc[index].FromNode
                    all_edges.loc[(all_edges['FromNode'] == from_node) & (all_edges['FromEdges'] == ""),
                    'OriginVertex'] = vertex_name
                    all_edges.loc[(all_edges['ToNode'] == from_node) & (all_edges['ToEdges'] == ""),
                    'DestinVertex'] = vertex_name

            if not all_edges.loc[index].DestinVertex:  # fresh edge that doesn't have destination vertices assigned
                # create and add destination vertex to graph
                vertex_name = 'visnode.' + str(all_edges.loc[index].ToNode) + '.' + str(index)
                self.add_vertex(name=vertex_name)

                # add this edge's destination vertex as OriginVertex of all edges going from it
                vertex_exit_edges = all_edges.loc[index].ToEdges
                if vertex_exit_edges:
                    vertex_exit_edges = [int(ed) for ed in vertex_exit_edges.split(',')]
                    all_edges.loc[vertex_exit_edges, 'OriginVertex'] = vertex_name
                    # add the vertex to the DestinVertex of other edges coming from the same edges
                    vertex_enter_edges = [ed.split(',') for ed in all_edges.loc[vertex_exit_edges].FromEdges]
                    vertex_enter_edges = [int(ed) for ed in itertools.chain.from_iterable(vertex_enter_edges)]
                    all_edges.loc[vertex_enter_edges, 'DestinVertex'] = vertex_name
                else:  # add vertex to all edges going directly to and from node
                    to_node = all_edges.loc[index].ToNode
                    all_edges.loc[(all_edges['FromNode'] == to_node) & (all_edges['FromEdges'] == ""),
                    'OriginVertex'] = vertex_name
                    all_edges.loc[(all_edges['ToNode'] == to_node) & (all_edges['ToEdges'] == ""),
                    'DestinVertex'] = vertex_name

            # add this edge to the graph
            # if not all_edges.loc[index, 'Closed']: # TODO apply closed status during edge cost analysis
            self.add_edge(all_edges.loc[index, 'OriginVertex'],
                          all_edges.loc[index, 'DestinVertex'],
                          name="visedge." + str(index))

        return all_edges


# Testing code
if __name__ == "__main__":
    Vissim = com.gencache.EnsureDispatch("Vissim.Vissim")
    from win32com.client import constants as c

    FileName = r"C:\Users\Public\Documents\PTV Vision\PTV Vissim 9\Examples Demo\Urban Freeway Dyn Assign Redmond.US\I405 OD"
    # FileName = r"E:\Thesis\Inital test network"
    Vissim.LoadNet(FileName + ".inpx")
    Net = Vissim.Net
    if not Net.DynamicAssignment.CreateGraph(c.CGEdgeTypeDynamicAssignment):
        print("VISSIM Network Graph Creation error")
        exit(1)

    road_graph = VissimRoadNet(Net)
    road_graph.write_svg(r"E:\Thesis\test.svg", width=3000, height=3000)
    Vissim.Exit()
