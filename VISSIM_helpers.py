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
        self.vissim_net_to_igraph(net)

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
        all_edges.No = all_edges.No.astype('int32')
        all_edges.FromNode = all_edges.FromNode.astype('int32')
        all_edges.ToNode = all_edges.ToNode.astype('int32')
        all_edges.set_index('No', inplace=True, verify_integrity=True, drop=False)
        all_edges.astype({
            'FromEdges': str,
            'ToEdges': str,
            'IsTurn': bool,
            'Type': 'category',
            'Closed': bool
        }, copy=False)
        all_edges['OriginVertex'] = ""
        all_edges['DestinVertex'] = ""

        # read each edge into graph, build vertices as we go
        for index, edge in all_edges.iterrows():
            pass


# Testing code
if __name__ == "__main__":
    Vissim = com.gencache.EnsureDispatch("Vissim.Vissim")
    from win32com.client import constants as c

    FileName = r"C:\Users\Public\Documents\PTV Vision\PTV Vissim 9\Examples Demo\Urban Freeway Dyn Assign Redmond.US\I405 OD"
    Vissim.LoadNet(FileName + ".inpx")
    #Vissim.LoadLayout(FileName + ".layx")
    Net = Vissim.Net
    if not Net.DynamicAssignment.CreateGraph(c.CGEdgeTypeDynamicAssignment):
        print("VISSIM Network Graph Creation error")
        exit(1)

    road_graph = VissimRoadNet(Net)
    road_graph.write_svg(r"E:\Thesis\test.svg")
