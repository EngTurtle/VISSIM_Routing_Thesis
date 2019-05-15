import igraph
import win32com.client as com
import pandas as pd


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
        self.net = net
        self.visedges = self.vissim_net_to_igraph(self.net)

    def vissim_net_to_igraph(self, vissim_net):
        """
        This function takes in a VISSIM network COM object, then reads it and converts it to a VissimRoadNet object
        :param vissim_net: win32com.gen_py.[VISSIM COM GUID].INet
        :return:
        """
        assert type(vissim_net).__name__ == "INet"

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
                all_edges.loc[index, 'OriginVertex'] = vertex_name

            # add this edge's origin vertex as DestinVertex of all edges going into it
            from_edges = all_edges.loc[index].FromEdges
            if from_edges:
                from_edges = [int(ed) for ed in from_edges.split(',')]
                all_edges.loc[from_edges, 'DestinVertex'] = all_edges.loc[index, 'OriginVertex']
                # TODO add the vertex to the OriginVertex of other edges going to the same edges

            if not all_edges.loc[index].DestinVertex:  # fresh edge that doesn't have destination vertices assigned
                # create and add destination vertex to graph
                vertex_name = 'visnode.' + str(all_edges.loc[index].ToNode) + '.' + str(index)
                self.add_vertex(name=vertex_name)
                all_edges.loc[index, 'DestinVertex'] = vertex_name

            # add this edge's destination vertex as OriginVertex of all edges going from it
            to_edges = all_edges.loc[index].ToEdges
            if to_edges:
                to_edges = [int(ed) for ed in to_edges.split(',')]
                all_edges.loc[to_edges, 'OriginVertex'] = all_edges.loc[index, 'DestinVertex']
                # TODO add the vertex to the DestinVertex of other edges coming from the same edges

            # add this edge to the graph
            if not all_edges.loc[index, 'Closed']:
                self.add_edge(all_edges.loc[index, 'OriginVertex'],
                              all_edges.loc[index, 'DestinVertex'],
                              name="visedge." + str(index))

        return all_edges


# Testing code
if __name__ == "__main__":
    Vissim = com.gencache.EnsureDispatch("Vissim.Vissim")
    from win32com.client import constants as c

    FileName = r"C:\Users\Public\Documents\PTV Vision\PTV Vissim 9\Examples Demo\Urban Freeway Dyn Assign Redmond.US\I405 OD"
    Vissim.LoadNet(FileName + ".inpx")
    Net = Vissim.Net
    if not Net.DynamicAssignment.CreateGraph(c.CGEdgeTypeDynamicAssignment):
        print("VISSIM Network Graph Creation error")
        exit(1)

    road_graph = VissimRoadNet(Net)
    road_graph.write_svg(r"E:\Thesis\test.svg")
    Vissim.Exit()
