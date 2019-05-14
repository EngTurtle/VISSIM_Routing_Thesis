import igraph
import win32com.client as com
import pandas as pd


class VissimRoadNet(igraph.Graph):
    """
    This class extends the igraph Graph object to allow connection with a VISSIM
    """
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

        # read edges into pandas list
        edge_attributes = ['No', 'FromNode', 'ToNode', 'FromEdges', 'ToEdges', 'IsTurn', 'Type', 'Closed']
        all_edges = pd.DataFrame([list(row) for row in vissim_net.Edges.GetMultipleAttributes(edge_attributes)],
                                 columns=edge_attributes)
        all_edges["GraphFromNode"] = ""  # add column for node assignment later
        all_edges["GraphToNode"] = ""

        non_turn_edges = all_edges[(all_edges.Closed == 0) &
                                   (all_edges.Type == 'DYNAMICASSIGNMENT') &
                                   (all_edges.IsTurn == 0)]
        turn_edges = all_edges[(all_edges.Closed == 0) &
                               (all_edges.Type == 'DYNAMICASSIGNMENT') &
                               (all_edges.IsTurn == 1)]

        # read nodes and add as vertex of graph
        node_attributes = ['No', 'Name', 'UseForDynAssign']
        for node_no, node_name, node_assign in vissim_net.Nodes.GetMultipleAttributes(node_attributes):
            node_no = str(node_no)
            if node_assign:  # only dynamic assignment nodes
                if turn_edges[turn_edges.FromNode == node_no].shape[0] > 0:  # if the node has turn edges
                    # add entrance vertices
                    for edge_index, entering_edge in non_turn_edges[non_turn_edges.ToNode == node_no].iterrows():
                        graph_node_name = "visnode." + node_no + '.' + str(entering_edge.No)
                        self.add_vertex(name=graph_node_name)
                        non_turn_edges.at[edge_index, 'GraphToNode'] = graph_node_name
                        turn_edges.at[turn_edges.FromEdges == str(entering_edge.No), 'GraphFromNode'] = graph_node_name

                    # add exit vertices
                    for edge_index, exiting_edge in non_turn_edges[non_turn_edges.FromNode == node_no].iterrows():
                        graph_node_name = "visnode." + node_no + '.' + str(exiting_edge.No)
                        self.add_vertex(name=graph_node_name)
                        non_turn_edges.at[edge_index, 'GraphFromNode'] = graph_node_name
                        turn_edges.at[turn_edges.ToEdges == str(exiting_edge.No), 'GraphToNode'] = graph_node_name

                else:  # if the node doesn't have turn edges
                    graph_node_name = "visnode." + node_no + '.0'
                    self.add_vertex(name=graph_node_name)
                    non_turn_edges.at[non_turn_edges.FromNode == node_no, 'GraphFromNode'] = graph_node_name
                    non_turn_edges.at[non_turn_edges.ToNode == node_no, 'GraphToNode'] = graph_node_nameyt


        # add edges to graph
        for _, edge in non_turn_edges.iterrows():
            self.add_edge(edge.GraphFromNode, edge.GraphToNode, name='visedg.'+str(edge.No))
        for _, edge in turn_edges.iterrows():
            self.add_edge(edge.GraphFromNode, edge.GraphToNode, name='visedg.'+str(edge.No))


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
