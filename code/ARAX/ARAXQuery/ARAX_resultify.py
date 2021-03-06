#!/usr/bin/env python3
'''This module defines the `ARAXResultify` class whose `_resultify` method
enumerates subgraphs of a knowledge graph (KG) that match a pattern set by a
query graph (QG) and sets the `results` data attribute of the `message` object
to be a list of `Result` objects, each corresponding to one of the enumerated
subgraphs. The matching between the KG subgraphs and the QG can be forced to be
sensitive to edge direction by setting `ignore_edge_direction=false` (the
default is to ignore edge direction).

   Usage: python3 -u ARAX_resultify.py

   will run the built-in tests for ARAX_resultify.py. When testing, also be sure
   to run the `document_dsl_commands.py` script in the `code/ARAX/Documentation`
   directory since that script uses the `describe_me` method of this module.

'''

import collections
import math
import os
import sys
from typing import List, Dict, Set, Union, Iterable, cast, Optional
from response import Response

__author__ = 'Stephen Ramsey and Amy Glen'
__copyright__ = 'Oregon State University'
__credits__ = ['Stephen Ramsey', 'Amy Glen', 'David Koslicki', 'Eric Deutsch']
__license__ = 'MIT'
__version__ = '0.1.0'
__maintainer__ = 'Amy Glen'
__email__ = ''
__status__ = 'Prototype'


# is there a better way to import swagger_server?  Following SO posting 16981921
PACKAGE_PARENT = '../../UI/OpenAPI/python-flask-server'
sys.path.append(os.path.normpath(os.path.join(os.getcwd(), PACKAGE_PARENT)))
from swagger_server.models.edge import Edge
from swagger_server.models.node import Node
from swagger_server.models.q_edge import QEdge
from swagger_server.models.q_node import QNode
from swagger_server.models.query_graph import QueryGraph
from swagger_server.models.knowledge_graph import KnowledgeGraph
from swagger_server.models.node_binding import NodeBinding
from swagger_server.models.edge_binding import EdgeBinding
from swagger_server.models.biolink_entity import BiolinkEntity
from swagger_server.models.result import Result
from swagger_server.models.message import Message


# define a string-parameterized BiolinkEntity class
class BiolinkEntityStr(BiolinkEntity):
    def __init__(self, category_label: str):
        super().__init__()
        self.category_label = category_label

    def __str__(self):
        return super().__str__() + ":" + self.category_label


# define a map between category_label and BiolinkEntity object
BIOLINK_CATEGORY_LABELS = {'protein', 'disease', 'phenotypic_feature', 'gene', 'chemical_substance'}
BIOLINK_ENTITY_TYPE_OBJECTS = {category_label: BiolinkEntityStr(category_label) for
                               category_label in BIOLINK_CATEGORY_LABELS}


class ARAXResultify:
    ALLOWED_PARAMETERS = {'debug', 'ignore_edge_direction'}

    def __init__(self):
        self.response = None
        self.message = None
        self.parameters = None

    def describe_me(self):
        """
        Little helper function for internal use that describes the actions and what they can do
        :return:
        """

        brief_description = """ Creates a list of results from the input query graph (QG) based on the the
information contained in the message knowledge graph (KG). Every subgraph
through the KG that satisfies the GQ is returned. Such use cases include:
- `resultify()` Returns all subgraphs in the knowledge graph that satisfy the
  query graph
- `resultiy(ignore_edge_direction=false)` This mode checks edge directions in
the QG to ensure that matching an edge in the KG to an edge in the QG is only
allowed if the two edges point in the same direction. The default is to not
check edge direction. For example, you may want to include results that include
relationships like `(protein)-[involved_in]->(pathway)` even though the
underlying KG only contains directional edges of the form
`(protein)<-[involved_in]-(pathway)`.  Note that this command will successfully
execute given an arbitrary query graph and knowledge graph provided by the
automated reasoning system, not just ones generated by Team ARA Expander."""
        description_list = []
        params_dict = dict()
        params_dict['brief_description'] = brief_description
        params_dict['ignore_edge_direction'] = {'''`true` or `false`. Optional; default is `true`.'''}
        # TODO: will need to update manually if more self.parameters are added
        # eg. params_dict[node_id] = {"a query graph node ID or list of such id's (required)"} as per issue #640
        description_list.append(params_dict)
        return description_list

    def apply(self, input_message: Message, input_parameters: dict) -> Response:

        # Define a default response
        response = Response()
        self.response = response
        self.message = input_message

        # Basic checks on arguments
        if not isinstance(input_parameters, dict):
            response.error("Provided parameters is not a dict", error_code="ParametersNotDict")
            return response

        # Return if any of the parameters generated an error (showing not just the first one)
        if response.status != 'OK':
            return response

        # Store these final parameters for convenience
        response.data['parameters'] = input_parameters
        self.parameters = input_parameters

        response.debug(f"Applying Resultifier to Message with parameters {input_parameters}")

        # call _resultify
        self._resultify(describe=False)

        # Clean up the KG (should only contain nodes used in the results)
        self._clean_up_kg()

        # Return the response and done
        return response

    def _resultify(self, describe: bool = False):
        """From a knowledge graph and a query graph (both in a Message object), extract a list of Results objects, each containing
        lists of NodeBinding and EdgeBinding objects. Add a list of Results objects to self.message.rseults.

        It is required that `self.parameters` contain the following:
            ignore_edge_direction: a parameter of type `bool` indicating whether
            the direction of an edge in the knowledge graph should be taken into
            account when matching that edge to an edge in the query graph. By
            default, this parameter is `true`. Set this parameter to false in
            order to require that an edge in a subgraph of the KG will only
            match an edge in the QG if both have the same direction (taking into
            account the source/target node mapping). Optional.

        """
        assert self.response is not None
        results = self.message.results
        if results is not None and len(results) > 0:
            self.response.info(f"Clearing previous results and computing a new set of results")
            self.message.results = []
            results = self.message.results
            self.message.n_results = 0

        message = self.message
        parameters = self.parameters

        debug_mode = parameters.get('debug', None)
        if debug_mode is not None:
            try:
                debug_mode = _parse_boolean_case_insensitive(debug_mode)
            except Exception as e:
                self.response.error(str(e))
                return

        for parameter_name in parameters.keys():
            if parameter_name == '':
                continue
            if parameter_name not in ARAXResultify.ALLOWED_PARAMETERS:
                error_string = "parameter type is not allowed in ARAXResultify: " + str(parameter_name)
                if not debug_mode:
                    self.response.error(error_string)
                    return
                else:
                    raise ValueError(error_string)

        kg = message.knowledge_graph
        qg = message.query_graph
        ignore_edge_direction = parameters.get('ignore_edge_direction', None)
        if ignore_edge_direction is not None:
            try:
                ignore_edge_direction = _parse_boolean_case_insensitive(ignore_edge_direction)
            except ValueError as e:
                error_string = "parameter value is not allowed in ARAXResultify: " + str(ignore_edge_direction)
                if not debug_mode:
                    self.response.error(error_string)
                    return
                else:
                    raise e

        try:
            results = _get_results_for_kg_by_qg(kg,
                                                qg,
                                                ignore_edge_direction)
            message_code = 'OK'
            code_description = 'Result list computed from KG and QG'
        except Exception as e:
            if not debug_mode:
                code_description = str(e)
                message_code = e.__class__.__name__
                self.response.error(code_description)
                results = []
            else:
                raise e

        message.results = results
        if len(results) == 0 and message_code == 'OK':
            message_code = 'WARNING'
            code_description = 'no results returned'
            if len(kg.nodes) == 0:
                code_description += '; empty knowledge graph'
            self.response.warning(code_description)
        elif message_code == 'OK':
            self.response.info(f"Resultify created {len(results)} results")

        message.n_results = len(results)
        message.code_description = code_description
        message.message_code = message_code

    def _clean_up_kg(self):
        self.response.debug(f"Cleaning up the KG to remove nodes not used in the results")
        results = self.message.results
        kg = self.message.knowledge_graph
        node_ids_used_in_results = {node_binding.kg_id for result in results for node_binding in result.node_bindings}
        cleaned_kg = KnowledgeGraph(nodes=[node for node in kg.nodes if node.id in node_ids_used_in_results],
                                    edges=[edge for edge in kg.edges if {edge.source_id, edge.target_id}.issubset(node_ids_used_in_results)])
        self.message.knowledge_graph = cleaned_kg
        self.response.info(f"After cleaning, the KG contains {len(self.message.knowledge_graph.nodes)} nodes and "
                           f"{len(self.message.knowledge_graph.edges)} edges")


def _make_edge_key(node1_id: str,
                   node2_id: str) -> str:
    return node1_id + '->' + node2_id


def _is_specific_query_node(qnode: QNode):
    return (qnode.id is not None and ':' in qnode.id) or \
        (qnode.curie is not None and ':' in qnode.curie)


def _make_adj_maps(graph: Union[QueryGraph, KnowledgeGraph],
                   directed=True,
                   droploops=True) -> Dict[str, Dict[str, Set[str]]]:
    if directed:
        adj_map_in: Dict[str, Set[str]] = {node.id: set() for node in graph.nodes}
        adj_map_out: Dict[str, Set[str]] = {node.id: set() for node in graph.nodes}
    else:
        adj_map: Dict[str, Set[str]] = {node.id: set() for node in graph.nodes}
    try:
        for edge in graph.edges:
            if droploops and edge.target_id == edge.source_id:
                continue
            if directed:
                edge_node_id = edge.source_id
                adj_map_out[edge_node_id].add(edge.target_id)
                edge_node_id = edge.target_id
                adj_map_in[edge_node_id].add(edge.source_id)
            else:
                edge_node_id = edge.source_id
                adj_map[edge_node_id].add(edge.target_id)
                edge_node_id = edge.target_id
                adj_map[edge_node_id].add(edge.source_id)
    except KeyError:
        raise ValueError("Graph has an edge " + str(edge) + " that refers to a node ID (" + edge_node_id + ") that is not in the graph")
    if directed:
        ret_dict = {'in': adj_map_in, 'out': adj_map_out}
    else:
        ret_dict = {'both': adj_map}
    return ret_dict


def _bfs_dists(adj_map: Dict[str, Set[str]],
               start_node_id: str) -> Dict[str, Union[int, float]]:
    queue = collections.deque([start_node_id])
    distances = {node_id: math.inf for node_id in adj_map.keys()}
    distances[start_node_id] = 0
    while len(queue) > 0:
        node_id = queue.popleft()
        node_dist = distances[node_id]
        assert not math.isinf(node_dist)
        for neighb_node_id in cast(Iterable[str], adj_map[node_id]):
            if math.isinf(distances[neighb_node_id]):
                distances[neighb_node_id] = node_dist + 1
                queue.append(neighb_node_id)
    return distances


def _get_essence_node_for_qg(qg: QueryGraph) -> Optional[str]:
    adj_map = _make_adj_maps(qg, directed=False)['both']
    node_ids_list = list(adj_map.keys())
    all_nodes = set(node_ids_list)
    node_degrees = list(map(len, adj_map.values()))
    leaf_nodes = set(node_ids_list[i] for i, k in enumerate(node_degrees) if k == 1)
    is_set_nodes = set(node.id for node in cast(Iterable[QNode], qg.nodes) if node.is_set)
    specific_nodes = set(node.id for node in cast(Iterable[QNode], qg.nodes) if _is_specific_query_node(node))
    non_specific_nodes = all_nodes - specific_nodes
    non_specific_leaf_nodes = leaf_nodes & non_specific_nodes

    if len(is_set_nodes & specific_nodes) > 0:
        raise ValueError("the following query nodes have specific CURIE IDs but have is_set=true: " + str(is_set_nodes & specific_nodes))
    candidate_essence_nodes = non_specific_leaf_nodes - is_set_nodes
    if len(candidate_essence_nodes) == 0:
        candidate_essence_nodes = non_specific_nodes - is_set_nodes
    if len(candidate_essence_nodes) == 0:
        return None
    elif len(candidate_essence_nodes) == 1:
        return next(iter(candidate_essence_nodes))
    else:
        specific_leaf_nodes = specific_nodes & leaf_nodes
        if len(specific_leaf_nodes) == 0:
            map_node_id_to_pos: Dict[str, Union[int, float]] = {node.id: i for i, node in enumerate(cast(Iterable[QNode], qg.nodes))}
            if len(specific_nodes) == 0:
                # return the node.id of the non-specific node with the rightmost position in the QG node list
                return sorted(candidate_essence_nodes,
                              key=lambda node_id: map_node_id_to_pos[node_id],
                              reverse=True)[0]
            else:
                if len(specific_nodes) == 1:
                    specific_node_id = next(iter(specific_nodes))
                    return sorted(candidate_essence_nodes,
                                  key=lambda node_id: abs(map_node_id_to_pos[node_id] -
                                                          map_node_id_to_pos[specific_node_id]),
                                  reverse=True)[0]
                else:
                    # there are at least two non-specific leaf nodes and at least two specific nodes
                    return sorted(candidate_essence_nodes,
                                  key=lambda node_id: min([abs(map_node_id_to_pos[node_id] -
                                                               map_node_id_to_pos[specific_node_id]) for
                                                           specific_node_id in specific_nodes]),
                                  reverse=True)[0]
        else:
            if len(specific_leaf_nodes) == 1:
                specific_leaf_node_id = next(iter(specific_leaf_nodes))
                map_node_id_to_pos = _bfs_dists(adj_map, specific_leaf_node_id)
            else:
                all_dist_maps_for_spec_leaf_nodes = {node_id: _bfs_dists(adj_map,
                                                                         node_id) for
                                                     node_id in specific_leaf_nodes}
                map_node_id_to_pos = {node.id: min([dist_map[node.id] for dist_map in all_dist_maps_for_spec_leaf_nodes.values()]) for
                                      node in cast(Iterable[QNode], qg.nodes)}
            return sorted(candidate_essence_nodes,
                          key=lambda node_id: map_node_id_to_pos[node_id],
                          reverse=True)[0]
    assert False


def _parse_boolean_case_insensitive(input_string:  str) -> bool:
    if input_string is None:
        raise ValueError("invalid value for input_string")
    input_string = input_string.lower()
    if input_string == 'true':
        return True
    elif input_string == 'false':
        return False
    else:
        raise ValueError("invalid value for input_string")


def _get_results_for_kg_by_qg(kg: KnowledgeGraph,              # all nodes *must* have qnode_id specified
                              qg: QueryGraph,
                              ignore_edge_direction: bool = True) -> List[Result]:

    if ignore_edge_direction is None:
        return _get_results_for_kg_by_qg(kg, qg)

    if len([node.id for node in cast(Iterable[QNode], qg.nodes) if node.id is None]) > 0:
        raise ValueError("node has None for node.id in query graph")

    if len([node.id for node in cast(Iterable[Node], kg.nodes) if node.id is None]) > 0:
        raise ValueError("node has None for node.id in knowledge graph")

    kg_node_ids_without_qnode_id = [node.id for node in cast(Iterable[Node], kg.nodes) if not node.qnode_ids]
    if len(kg_node_ids_without_qnode_id) > 0:
        raise ValueError("these node IDs do not have qnode_ids set: " + str(kg_node_ids_without_qnode_id))

    kg_edge_ids_without_qedge_id = [edge.id for edge in cast(Iterable[Edge], kg.edges) if not edge.qedge_ids]
    if len(kg_edge_ids_without_qedge_id) > 0:
        raise ValueError("these edges do not have qedge_ids set: " + str(kg_edge_ids_without_qedge_id))

    kg_edge_ids_by_qg_id = _get_kg_edge_ids_by_qg_id(kg)
    kg_node_ids_by_qg_id = _get_kg_node_ids_by_qg_id(kg)

    # build up maps of node IDs to nodes, for both the KG and QG
    kg_nodes_map = {node.id: node for node in cast(Iterable[Node], kg.nodes)}
    qg_nodes_map = {node.id: node for node in cast(Iterable[QNode], qg.nodes)}

    # build up maps of edge IDs to edges, for both the KG and QG
    kg_edges_map = {edge.id: edge for edge in cast(Iterable[Edge], kg.edges)}
    qg_edges_map = {edge.id: edge for edge in cast(Iterable[QEdge], qg.edges)}

    # --------------------- checking for validity of the NodeBindings list --------------
    # we require that every query graph node ID in the "values" slot of the node_bindings_map corresponds to an actual node in the QG
    qnode_ids_mapped_that_are_not_in_qg = [qnode_id for qnode_id in kg_node_ids_by_qg_id if qnode_id not in qg_nodes_map]
    if len(qnode_ids_mapped_that_are_not_in_qg) > 0:
        raise ValueError("A node in the KG has a qnode_id that does not exist in the QueryGraph: " + str(qnode_ids_mapped_that_are_not_in_qg))

    # --------------------- checking for validity of the EdgeBindings list --------------
    # we require that every query graph edge ID in the "values" slot of the edge_bindings_map corresponds to an actual edge in the QG
    qedge_ids_mapped_that_are_not_in_qg = [qedge_id for qedge_id in kg_edge_ids_by_qg_id if qedge_id not in qg_edges_map]
    if len(qedge_ids_mapped_that_are_not_in_qg) > 0:
        raise ValueError("An edge in the KG has a qedge_id that does not exist in the QueryGraph: " + str(qedge_ids_mapped_that_are_not_in_qg))

    # --------------------- checking that the source ID and target ID of every edge in KG is a valid KG node ---------------------
    node_ids_for_edges_that_are_not_valid_nodes = [edge.source_id for edge in cast(Iterable[Edge], kg.edges) if not
                                                   kg_nodes_map.get(edge.source_id)] + \
                                                  [edge.target_id for edge in cast(Iterable[Edge], kg.edges) if not
                                                   kg_nodes_map.get(edge.target_id)]
    if len(node_ids_for_edges_that_are_not_valid_nodes) > 0:
        raise ValueError("KG has Edges that refer to the following non-existent Nodes: " + str(node_ids_for_edges_that_are_not_valid_nodes))

    # --------------------- checking that the source ID and target ID of every edge in QG is a valid QG node ---------------------
    invalid_qnode_ids_used_by_qedges = [edge.source_id for edge in cast(Iterable[QEdge], qg.edges) if not
                                        qg_nodes_map.get(edge.source_id)] + \
                                       [edge.target_id for edge in cast(Iterable[QEdge], qg.edges) if not
                                        qg_nodes_map.get(edge.target_id)]
    if len(invalid_qnode_ids_used_by_qedges) > 0:
        raise ValueError("QG has QEdges that refer to the following non-existent QNodes: " + str(invalid_qnode_ids_used_by_qedges))

    # --------------------- checking for consistency of edge-to-node relationships, for all edge bindings -----------
    # check that for each bound KG edge, the QG mappings of the KG edges source and target nodes are also the
    # source and target nodes of the QG edge that corresponds to the bound KG edge
    for qedge_id, kg_edge_ids_for_this_qedge_id in kg_edge_ids_by_qg_id.items():
        qg_edge = next(qedge for qedge in qg.edges if qedge.id == qedge_id)
        qg_source_node_id = qg_edge.source_id
        qg_target_node_id = qg_edge.target_id
        for edge_id in kg_edge_ids_for_this_qedge_id:
            kg_edge = kg_edges_map.get(edge_id)
            kg_source_node_id = kg_edge.source_id
            kg_target_node_id = kg_edge.target_id
            if qg_source_node_id != qg_target_node_id:
                edge_valid_in_same_direction = (kg_source_node_id in kg_node_ids_by_qg_id[qg_source_node_id] and
                                                kg_target_node_id in kg_node_ids_by_qg_id[qg_target_node_id])
                edge_valid_in_opposite_direction = (kg_source_node_id in kg_node_ids_by_qg_id[qg_target_node_id] and
                                                    kg_target_node_id in kg_node_ids_by_qg_id[qg_source_node_id])
                edge_is_valid = (edge_valid_in_same_direction or edge_valid_in_opposite_direction) if ignore_edge_direction else edge_valid_in_same_direction
                if not edge_is_valid:
                    kg_source_node = kg_nodes_map.get(kg_source_node_id)
                    kg_target_node = kg_nodes_map.get(kg_target_node_id)
                    raise ValueError(f"Edge {kg_edge.id} (fulfilling {qg_edge.id}) has node(s) that do not fulfill the "
                                     f"expected qnodes ({qg_source_node_id} and {qg_target_node_id}). Edge's nodes are "
                                     f"{kg_source_node_id} (qnode_ids: {kg_source_node.qnode_ids}) and "
                                     f"{kg_target_node_id} (qnode_ids: {kg_target_node.qnode_ids}).")

    # ============= save until SAR can discuss with {EWD,DMK} whether there can be unmapped nodes in the KG =============
    # # if any node in the KG is not bound to a node in the QG, drop the KG node; redefine "kg" as the filtered KG
    # kg_node_ids_keep = {node.id for node in kg.nodes if node.id in node_bindings_map}
    # kg_nodes_keep_list = [node for node in kg.nodes if node.id in kg_node_ids_keep]
    # kg_edges_keep_list = [edge for edge in kg.edges if not (edge.source_id in kg_node_ids_keep and
    #                                                         edge.target_id in kg_node_ids_keep)]
    # kg = KnowledgeGraph(nodes=kg_nodes_keep_list,
    #                     edges=kg_edges_keep_list)
    # ============= save until SAR can discuss with {EWD,DMK} whether there can be unmapped nodes in the KG =============

    # Our goal is to enumerate all distinct "edge-maximal" subgraphs of the KG that each "covers"
    # the QG. A subgraph of KG that "covers" the QG is one for which all of the following conditions hold:
    # (1) under the KG-to-QG node bindings map, the range of the KG subgraph's nodes is the entire set of nodes in the QG
    # (2) for any QG node that has "is_set=True", *all* KG nodes that are bound to the same QG node are in the subgraph
    # (3) every edge in the QG is "covered" by at least one edge in the KG

    results: List[Result] = []

    # Return empty result list if the QG isn't fulfilled
    unfulfilled_qnode_ids = [qnode.id for qnode in qg.nodes if not kg_node_ids_by_qg_id.get(qnode.id)]
    unfulfilled_qedge_ids = [qedge.id for qedge in qg.edges if not kg_edge_ids_by_qg_id.get(qedge.id)]
    if unfulfilled_qnode_ids or unfulfilled_qedge_ids or not kg.nodes:
        return results

    results = _create_results(kg, qg, ignore_edge_direction)

    return results


def _get_connected_qnode(qnode_id: str, qnode_ids_to_choose_from: [str], query_graph: QueryGraph) -> Optional[str]:
    for qedge in query_graph.edges:
        if qedge.source_id == qnode_id and qedge.target_id in qnode_ids_to_choose_from:
            return qedge.target_id
        elif qedge.target_id == qnode_id and qedge.source_id in qnode_ids_to_choose_from:
            return qedge.source_id
    return None


def _get_query_node(qnode_id: str, query_graph: QueryGraph) -> QNode:
    for qnode in query_graph.nodes:
        if qnode.id == qnode_id:
            return qnode
    return None


def _get_query_edge(qedge_id: str, query_graph: QueryGraph) -> QEdge:
    for qedge in query_graph.edges:
        if qedge.id == qedge_id:
            return qedge
    return None


def _get_qnodes_in_order(query_graph: QueryGraph) -> List[QNode]:
    if len(query_graph.edges) == 0:
        return [query_graph.nodes[0]]
    elif len(query_graph.edges) == 1:
        qedge = query_graph.edges[0]
        return [_get_query_node(qedge.source_id, query_graph), _get_query_node(qedge.target_id, query_graph)]
    else:
        qnode_ids_remaining = [qnode.id for qnode in query_graph.nodes]
        ordered_qnode_ids = []
        while qnode_ids_remaining:
            if not ordered_qnode_ids:
                starting_qnode_id = qnode_ids_remaining.pop()
                ordered_qnode_ids = [starting_qnode_id]
            else:
                new_right_most_qnode_id = _get_connected_qnode(ordered_qnode_ids[-1], qnode_ids_remaining, query_graph)
                new_left_most_qnode_id = _get_connected_qnode(ordered_qnode_ids[0], qnode_ids_remaining, query_graph)
                if new_right_most_qnode_id:
                    ordered_qnode_ids.append(new_right_most_qnode_id)
                    qnode_ids_remaining.pop(qnode_ids_remaining.index(new_right_most_qnode_id))
                elif new_left_most_qnode_id:
                    ordered_qnode_ids.insert(0, new_left_most_qnode_id)
                    qnode_ids_remaining.pop(qnode_ids_remaining.index(new_left_most_qnode_id))
                else:
                    disconnected_qnode_id = qnode_ids_remaining[0]
                    ordered_qnode_ids.append(disconnected_qnode_id)
                    qnode_ids_remaining.pop(qnode_ids_remaining.index(disconnected_qnode_id))
    return [_get_query_node(qnode_id, query_graph) for qnode_id in ordered_qnode_ids]


def _get_kg_node_ids_by_qg_id(knowledge_graph: KnowledgeGraph) -> Dict[str, Set[str]]:
    node_ids_by_qg_id = dict()
    for node in knowledge_graph.nodes:
        if node.qnode_ids:
            for qnode_id in node.qnode_ids:
                if qnode_id not in node_ids_by_qg_id:
                    node_ids_by_qg_id[qnode_id] = set()
                node_ids_by_qg_id[qnode_id].add(node.id)
    return node_ids_by_qg_id


def _get_kg_edge_ids_by_qg_id(knowledge_graph: KnowledgeGraph) -> Dict[str, Set[str]]:
    edge_ids_by_qg_id = dict()
    for edge in knowledge_graph.edges:
        if edge.qedge_ids:
            for qedge_id in edge.qedge_ids:
                if qedge_id not in edge_ids_by_qg_id:
                    edge_ids_by_qg_id[qedge_id] = set()
                edge_ids_by_qg_id[qedge_id].add(edge.id)
    return edge_ids_by_qg_id


def _get_connected_qnode_ids(qnode_id: str, query_graph: QueryGraph) -> Set[str]:
    qnode_ids_used_on_same_qedges = set()
    for qedge in query_graph.edges:
        qnode_ids_used_on_same_qedges.add(qedge.source_id)
        qnode_ids_used_on_same_qedges.add(qedge.target_id)
    return qnode_ids_used_on_same_qedges.difference({qnode_id})


def _create_new_empty_result_graph(query_graph: QueryGraph) -> Dict[str, Dict[str, Set[str]]]:
    empty_result_graph = {'nodes': {qnode.id: set() for qnode in query_graph.nodes},
                          'edges': {qedge.id: set() for qedge in query_graph.edges}}
    return empty_result_graph


def _copy_result_graph(result_graph: Dict[str, Dict[str, Set[str]]]) -> Dict[str, Dict[str, Set[str]]]:
    result_graph_copy = {'nodes': {qnode_id: node_ids for qnode_id, node_ids in result_graph['nodes'].items()},
                         'edges': {qedge_id: edge_ids for qedge_id, edge_ids in result_graph['edges'].items()}}
    return result_graph_copy


def _get_edge_node_pair_key(edge: Edge) -> str:
    return "--".join(sorted([edge.source_id, edge.target_id]))


def _get_parallel_qedge_ids(input_qedge: QEdge, query_graph: QueryGraph) -> Set[str]:
    input_qedge_node_ids = {input_qedge.source_id, input_qedge.target_id}
    parallel_qedge_ids = {qedge.id for qedge in query_graph.edges if {qedge.source_id, qedge.target_id} == input_qedge_node_ids}
    return parallel_qedge_ids


def _get_kg_node_adj_map_by_qg_id(kg_node_ids_by_qg_id: Dict[str, Set[str]], knowledge_graph: KnowledgeGraph, query_graph: QueryGraph) -> Dict[str, Dict[str, Dict[str, Set[str]]]]:
    # Returned dict looks like {'n00': {'CUI:11234': {'n01': {UniProtKB:122}}}}
    # First initiate the overall structure of our (QG-organized) adjacency map
    kg_node_to_node_map = {qnode_id: dict() for qnode_id in kg_node_ids_by_qg_id}
    for qnode_id, node_ids_set in kg_node_ids_by_qg_id.items():
        connected_qnode_ids = _get_connected_qnode_ids(qnode_id, query_graph)
        for node_id in node_ids_set:
            kg_node_to_node_map[qnode_id][node_id] = {connected_qnode_id: set() for connected_qnode_id in connected_qnode_ids}

    # Create a record of which qedge IDs are fulfilled between which node pairs
    node_pair_to_qedge_id_map = dict()
    for edge in knowledge_graph.edges:
        node_pair_key = _get_edge_node_pair_key(edge)
        if node_pair_key not in node_pair_to_qedge_id_map:
            node_pair_to_qedge_id_map[node_pair_key] = set()
        node_pair_to_qedge_id_map[node_pair_key] = node_pair_to_qedge_id_map[node_pair_key].union(set(edge.qedge_ids))

    # Fill out which KG nodes are connected to which
    for edge in knowledge_graph.edges:
        for qedge_id in edge.qedge_ids:
            qedge = _get_query_edge(qedge_id, query_graph)
            # Make sure ALL qedges between these two nodes have been fulfilled before marking them as 'connected'
            parallel_qedge_ids = _get_parallel_qedge_ids(qedge, query_graph)
            if parallel_qedge_ids.issubset(node_pair_to_qedge_id_map[_get_edge_node_pair_key(edge)]):
                qnode_id_1 = qedge.source_id
                qnode_id_2 = qedge.target_id
                if edge.source_id in kg_node_ids_by_qg_id[qnode_id_1] and edge.target_id in kg_node_ids_by_qg_id[qnode_id_2]:
                    kg_node_to_node_map[qnode_id_1][edge.source_id][qnode_id_2].add(edge.target_id)
                    kg_node_to_node_map[qnode_id_2][edge.target_id][qnode_id_1].add(edge.source_id)
                if edge.source_id in kg_node_ids_by_qg_id[qnode_id_2] and edge.target_id in kg_node_ids_by_qg_id[qnode_id_1]:
                    kg_node_to_node_map[qnode_id_2][edge.source_id][qnode_id_1].add(edge.target_id)
                    kg_node_to_node_map[qnode_id_1][edge.target_id][qnode_id_2].add(edge.source_id)
    return kg_node_to_node_map


def _result_graph_is_fulfilled(result_graph: Dict[str, Dict[str, Set[str]]], query_graph: QueryGraph) -> bool:
    for qnode in query_graph.nodes:
        if not result_graph['nodes'].get(qnode.id):
            return False
    for qedge in query_graph.edges:
        if not result_graph['edges'].get(qedge.id):
            return False
    return True


def _create_results(kg: KnowledgeGraph,
                    qg: QueryGraph,
                    ignore_edge_direction: bool = True) -> List[Result]:
    result_graphs = []
    kg_node_ids_by_qg_id = _get_kg_node_ids_by_qg_id(kg)
    kg_node_adj_map_by_qg_id = _get_kg_node_adj_map_by_qg_id(kg_node_ids_by_qg_id, kg, qg)
    kg_node_lookup = {node.id: node for node in kg.nodes}
    qnodes_in_order = _get_qnodes_in_order(qg)

    # First create result graphs with only the nodes filled out
    for qnode in qnodes_in_order:
        prior_qnode = qnodes_in_order[qnodes_in_order.index(qnode) - 1] if qnodes_in_order.index(qnode) > 0 else None
        if not result_graphs:
            all_node_ids_in_kg_for_this_qnode_id = kg_node_ids_by_qg_id.get(qnode.id)
            if qnode.is_set:
                new_result_graph = _create_new_empty_result_graph(qg)
                new_result_graph['nodes'][qnode.id] = all_node_ids_in_kg_for_this_qnode_id
                result_graphs.append(new_result_graph)
            else:
                for node_id in all_node_ids_in_kg_for_this_qnode_id:
                    new_result_graph = _create_new_empty_result_graph(qg)
                    new_result_graph['nodes'][qnode.id] = {node_id}
                    result_graphs.append(new_result_graph)
        else:
            new_result_graphs = []
            for result_graph in result_graphs:
                node_ids_for_prior_qnode_id = result_graph['nodes'][prior_qnode.id]
                connected_node_ids = set()
                for node_id in node_ids_for_prior_qnode_id:
                    connected_node_ids = connected_node_ids.union(kg_node_adj_map_by_qg_id[prior_qnode.id][node_id][qnode.id])
                if qnode.is_set:
                    new_result_graph = _copy_result_graph(result_graph)
                    new_result_graph['nodes'][qnode.id] = connected_node_ids
                    new_result_graphs.append(new_result_graph)
                else:
                    for node_id in connected_node_ids:
                        new_result_graph = _copy_result_graph(result_graph)
                        new_result_graph['nodes'][qnode.id] = {node_id}
                        new_result_graphs.append(new_result_graph)
            result_graphs = new_result_graphs

    # Then add edges to our result graphs as appropriate
    edges_by_node_pairs = {qedge.id: dict() for qedge in qg.edges}
    for edge in kg.edges:
        if edge.qedge_ids:
            for qedge_id in edge.qedge_ids:
                edge_node_pair = f"{edge.source_id}--{edge.target_id}"
                if edge_node_pair not in edges_by_node_pairs[qedge_id]:
                    edges_by_node_pairs[qedge_id][edge_node_pair] = set()
                edges_by_node_pairs[qedge_id][edge_node_pair].add(edge.id)
                if ignore_edge_direction:
                    node_pair_in_other_direction = f"{edge.target_id}--{edge.source_id}"
                    if node_pair_in_other_direction not in edges_by_node_pairs[qedge_id]:
                        edges_by_node_pairs[qedge_id][node_pair_in_other_direction] = set()
                    edges_by_node_pairs[qedge_id][node_pair_in_other_direction].add(edge.id)
    for result_graph in result_graphs:
        for qedge_id in result_graph['edges']:
            qedge = _get_query_edge(qedge_id, qg)
            potential_nodes_1 = result_graph['nodes'][qedge.source_id]
            potential_nodes_2 = result_graph['nodes'][qedge.target_id]
            possible_node_pairs = set()
            for node_1 in potential_nodes_1:
                for node_2 in potential_nodes_2:
                    node_pair_key = f"{node_1}--{node_2}"
                    possible_node_pairs.add(node_pair_key)
            for node_pair in possible_node_pairs:
                ids_of_matching_edges = edges_by_node_pairs[qedge_id].get(node_pair, set())
                result_graph['edges'][qedge_id] = result_graph['edges'][qedge_id].union(ids_of_matching_edges)

    final_result_graphs = [result_graph for result_graph in result_graphs if _result_graph_is_fulfilled(result_graph, qg)]

    # Convert these into actual object model results
    results = []
    for result_graph in final_result_graphs:
        node_bindings = []
        for qnode_id, node_ids in result_graph['nodes'].items():
            for node_id in node_ids:
                node_bindings.append(NodeBinding(qg_id=qnode_id, kg_id=node_id))
        edge_bindings = []
        for qedge_id, edge_ids in result_graph['edges'].items():
            for edge_id in edge_ids:
                edge_bindings.append(EdgeBinding(qg_id=qedge_id, kg_id=edge_id))
        result = Result(node_bindings=node_bindings, edge_bindings=edge_bindings)

        # Fill out the essence for the result
        essence_qnode_id = _get_essence_node_for_qg(qg)
        essence_qnode = _get_query_node(essence_qnode_id, qg)
        essence_kg_node_id_set = result_graph['nodes'].get(essence_qnode_id, set())
        if len(essence_kg_node_id_set) == 1:
            essence_kg_node_id = next(iter(essence_kg_node_id_set))
            essence_kg_node = kg_node_lookup[essence_kg_node_id]
            result.essence = essence_kg_node.name
            if result.essence is None:
                result.essence = essence_kg_node_id
            assert result.essence is not None
            if essence_kg_node.symbol is not None:
                result.essence += " (" + str(essence_kg_node.symbol) + ")"
            result.essence_type = str(essence_qnode.type) if essence_qnode else None
        elif len(essence_kg_node_id_set) == 0:
            result.essence = cast(str, None)
            result.essence_type = cast(str, None)
        else:
            raise ValueError(f"Result contains more than one node that is a candidate for the essence: {essence_kg_node_id_set}")

        # Programmatically generating an informative description for each result
        # seems difficult, but having something non-None is required by the
        # database.  Just put in a placeholder for now, as is done by the
        # QueryGraphReasoner
        result.description = "No description available"  # see issue 642

        results.append(result)

    return results




