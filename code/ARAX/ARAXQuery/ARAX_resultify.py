#!/usr/bin/env python3
'''This module defines the `ARAXResultify` class whose `_resultify` method
enumerates subgraphs of a knowledge graph (KG) that match a pattern set by a
query graph (QG) and sets the `results` data attribute of the `message` object
to be a list of `Result` objects, each corresponding to one of the enumerated
subgraphs. The matching between the KG subgraphs and the QG can be forced to be
sensitive to edge direction by setting `ignore_edge_direction=false` (the
default is to ignore edge direction). If any query nodes in the QG have the
`is_set` property set to `true`, this can be overridden in `resultify` by
including the query node `id` string (or the `id` fields of more than one query
node) in a parameter `force_isset_false` of type `List[str]`.

   Usage: python3 -u ARAX_resultify.py

   will run the built-in tests for ARAX_resultify.py. When testing, also be sure
   to run the `document_dsl_commands.py` script in the `code/ARAX/Documentation`
   directory since that script uses the `describe_me` method of this module.

'''

import collections
import itertools
import math
import os
import sys
from typing import List, Dict, Set, Union, Iterable, cast, Optional
from response import Response

__author__ = 'Stephen Ramsey'
__copyright__ = 'Oregon State University'
__credits__ = ['Stephen Ramsey', 'David Koslicki', 'Eric Deutsch', 'Amy Glen']
__license__ = 'MIT'
__version__ = '0.1.0'
__maintainer__ = ''
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
    ALLOWED_PARAMETERS = {'debug', 'force_isset_false', 'ignore_edge_direction'}

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
- `resultify(force_isset_false=[n01])` This forces each result to include only
  one example of node `n01` if it was originally part of a set in the QG. An
  example where one might use this mode is: suppose that the preceding DSL
  commands constructed a knowledge graph containing several proteins that are
  targets of a given drug, by making the protein node (suppose it is called
  `n01`) on the query graph have `is_set=true`. To extract one subgraph for each
  such protein, one would use `resultify(force_isset_false=[n01])`. The brackets
  around `n01` are because it is a list; in fact, multiple node IDs can be
  specified there, if they are separated by commas.
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
        params_dict['force_isset_false'] = {'''set of `id` strings of nodes in the QG. Optional; default = empty set.'''}
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

        # call _resultify
        self._resultify(describe=False)

        response.debug(f"Applying Resultifier to Message with parameters {input_parameters}")

        # Return the response and done
        return response

    def _resultify(self, describe: bool = False):
        """From a knowledge graph and a query graph (both in a Message object), extract a list of Results objects, each containing
        lists of NodeBinding and EdgeBinding objects. Add a list of Results objects to self.message.rseults.

        It is required that `self.parameters` contain the following:
            force_isset_false: a parameter of type `List[set]` containing string
            `id` fields of query nodes for which the `is_set` property should be
            set to `false`, overriding whatever the state of `is_set` for each
            of those nodes in the query graph. Optional.
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
        qg_nodes_override_treat_is_set_as_false_list = parameters.get('force_isset_false', None)
        if qg_nodes_override_treat_is_set_as_false_list is not None:
            qg_nodes_override_treat_is_set_as_false = set(qg_nodes_override_treat_is_set_as_false_list)
        else:
            qg_nodes_override_treat_is_set_as_false = set()
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
                                                qg_nodes_override_treat_is_set_as_false,
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

        message.n_results = len(results)
        message.code_description = code_description
        message.message_code = message_code


def _make_edge_key(node1_id: str,
                   node2_id: str) -> str:
    return node1_id + '->' + node2_id


def _make_result_from_node_set(dict_kg: KnowledgeGraph,
                               result_node_ids_by_qnode_id: Dict[str, Set[str]],
                               kg_edge_ids_by_qedge_id: Dict[str, Set[str]],
                               qg: QueryGraph) -> Result:
    node_bindings = []
    result_graph_node_ids = set()
    for qnode_id, node_ids_for_this_qnode_id in result_node_ids_by_qnode_id.items():
        for node_id in node_ids_for_this_qnode_id:
            node_bindings.append(NodeBinding(qg_id=qnode_id, kg_id=node_id))
            result_graph_node_ids.add(node_id)

    edge_bindings = []
    result_graph_edge_ids = set()
    for qedge_id, kg_edge_ids_for_this_qedge_id in kg_edge_ids_by_qedge_id.items():
        qedge = next(qedge for qedge in qg.edges if qedge.id == qedge_id)
        for edge_id in kg_edge_ids_for_this_qedge_id:
            edge = dict_kg.edges.get(edge_id)
            if ((edge.source_id in result_node_ids_by_qnode_id[qedge.source_id] and
                 edge.target_id in result_node_ids_by_qnode_id[qedge.target_id]) or
                (edge.source_id in result_node_ids_by_qnode_id[qedge.target_id] and
                 edge.target_id in result_node_ids_by_qnode_id[qedge.source_id])):
                edge_bindings.append(EdgeBinding(qg_id=qedge_id, kg_id=edge.id))
                result_graph_edge_ids.add(edge_id)

    result_graph = KnowledgeGraph(nodes=[dict_kg.nodes.get(node_id) for node_id in result_graph_node_ids],
                                  edges=[dict_kg.edges.get(edge_id) for edge_id in result_graph_edge_ids])
    result = Result(node_bindings=node_bindings,
                    edge_bindings=edge_bindings,
                    result_graph=result_graph)   #### FIXME: result_graph is deprecated and should no longer be used except for testing
    return result


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
                              qg_nodes_override_treat_is_set_as_false: set = None,
                              ignore_edge_direction: bool = True) -> List[Result]:

    if ignore_edge_direction is None:
        return _get_results_for_kg_by_qg(kg, qg, qg_nodes_override_treat_is_set_as_false)

    if len([node.id for node in cast(Iterable[QNode], qg.nodes) if node.id is None]) > 0:
        raise ValueError("node has None for node.id in query graph")

    if len([node.id for node in cast(Iterable[Node], kg.nodes) if node.id is None]) > 0:
        raise ValueError("node has None for node.id in knowledge graph")

    kg_node_ids_without_qnode_id = [node.id for node in cast(Iterable[Node], kg.nodes) if not node.qnode_ids]
    if len(kg_node_ids_without_qnode_id) > 0:
        raise ValueError("these node IDs do not have qnode_ids set: " + str(kg_node_ids_without_qnode_id))

    if qg_nodes_override_treat_is_set_as_false is None:
        qg_nodes_override_treat_is_set_as_false = set()

    # make a map of KG node IDs to QG node IDs, based on the node binding argument (nb) passed to this function
    node_bindings_map = {node.id: node.qnode_ids for node in cast(Iterable[Node], kg.nodes)}

    # make a map of KG edge IDs to QG edge IDs, based on the node binding argument (nb) passed to this function
    edge_bindings_map = {edge.id: edge.qedge_ids for edge in cast(Iterable[Edge], kg.edges) if edge.qedge_ids}

    qedge_ids_set = {edge.id for edge in cast(Iterable[QEdge], qg.edges)}
    kg_edge_ids_by_qedge_id = {qedge.id: {edge.id for edge in cast(Iterable[Edge], kg.edges) if edge.qedge_ids and qedge.id in edge.qedge_ids} for qedge in qg.edges}
    kg_node_ids_by_qnode_id = {qnode.id: {node.id for node in cast(Iterable[Node], kg.nodes) if node.qnode_ids and qnode.id in node.qnode_ids} for qnode in qg.nodes}

    # make a map of KG node ID to KG edges, by source:
    kg_adj_map_direc = _make_adj_maps(kg, directed=True, droploops=False)
    kg_node_id_incoming_adjacency_map = kg_adj_map_direc['in']
    kg_node_id_outgoing_adjacency_map = kg_adj_map_direc['out']

    # calling this method just for validation; it will raise a ValueError if the KG has an edge that refers to a node ID that is not in the KG
    _make_adj_maps(kg, directed=False, droploops=True)['both']

    # generate an adjacency map for the query graph
    qg_adj_map = _make_adj_maps(qg, directed=False, droploops=True)['both']  # can the QG have a self-loop?  not sure

    # build up maps of node IDs to nodes, for both the KG and QG
    kg_nodes_map = {node.id: node for node in cast(Iterable[Node], kg.nodes)}
    qg_nodes_map = {node.id: node for node in cast(Iterable[QNode], qg.nodes)}

    missing_node_ids = [node_id for node_id in qg_nodes_override_treat_is_set_as_false if node_id not in qg_nodes_map]
    if len(missing_node_ids) > 0:
        raise ValueError("the following nodes in qg_nodes_override_treat_is_set_as_false are not in the query graph: " +
                         str(missing_node_ids))

    # make an inverse "node bindings" map of QG node IDs to KG node ids
    reverse_node_bindings_map: Dict[str, set] = {node.id: set() for node in cast(Iterable[QNode], qg.nodes)}
    for node in cast(Iterable[Node], kg.nodes):
        for qnode_id in cast(Iterable[str], node.qnode_ids):
            reverse_node_bindings_map[qnode_id].add(node.id)

    # build up maps of edge IDs to edges, for both the KG and QG
    kg_edges_map = {edge.id: edge for edge in cast(Iterable[Edge], kg.edges)}
    qg_edges_map = {edge.id: edge for edge in cast(Iterable[QEdge], qg.edges)}

    # make a map between QG edge keys and QG edge IDs
    qg_edge_key_to_edge_id_map = {_make_edge_key(edge.source_id, edge.target_id): edge.id for edge in cast(Iterable[QEdge], qg.edges)}

    kg_undir_edge_keys_set = set(_make_edge_key(edge.source_id, edge.target_id) for edge in cast(Iterable[Edge], kg.edges)) |\
        set(_make_edge_key(edge.target_id, edge.source_id) for edge in cast(Iterable[Edge], kg.edges))

    # --------------------- checking for validity of the NodeBindings list --------------
    # we require that every query graph node ID in the "values" slot of the node_bindings_map corresponds to an actual node in the QG
    qnode_ids_mapped_that_are_not_in_qg = [qnode_id for qnode_id_list in node_bindings_map.values() for qnode_id in qnode_id_list if qnode_id not in qg_nodes_map]
    if len(qnode_ids_mapped_that_are_not_in_qg) > 0:
        raise ValueError("query node ID specified in the NodeBinding list that is not in the QueryGraph: " + str(qnode_ids_mapped_that_are_not_in_qg))

    # we require that every know. graph node ID in the "keys" slot of the node_bindings_map corresponds to an actual node in the KG
    node_ids_mapped_that_are_not_in_kg = [node_id for node_id in node_bindings_map.keys() if node_id not in kg_nodes_map]
    if len(node_ids_mapped_that_are_not_in_kg) > 0:
        raise ValueError("knowledge graph node ID specified in the NodeBinding list that is not in the KG: " + str(node_ids_mapped_that_are_not_in_kg))

    # --------------------- checking for validity of the EdgeBindings list --------------
    # we require that every query graph edge ID in the "values" slot of the edge_bindings_map corresponds to an actual edge in the QG
    qedge_ids_mapped_that_are_not_in_qg = [qedge_id for qedge_id_list in edge_bindings_map.values() for qedge_id in qedge_id_list if qedge_id_list and qedge_id not in qg_edges_map]
    if len(qedge_ids_mapped_that_are_not_in_qg) > 0:
        raise ValueError("query edge ID specified in the EdgeBinding list that is not in the QueryGraph: " + str(qedge_ids_mapped_that_are_not_in_qg))

    # we require that every know. graph edge ID in the "keys" slot of the edge_bindings_map corresponds to an actual edge in the KG
    edge_ids_mapped_that_are_not_in_kg = [edge_id for edge_id in edge_bindings_map.keys() if edge_id not in kg_edges_map]
    if len(edge_ids_mapped_that_are_not_in_kg) > 0:
        raise ValueError("knowledge graph edge ID specified in the EdgeBinding list that is not in the KG: " + str(edge_ids_mapped_that_are_not_in_kg))

    # --------------------- checking that the node bindings cover the query graph --------------
    # check if each node in the query graph are hit by at least one node binding; if not, raise an exception
    qg_ids_hit_by_bindings = {qnode_id for node in cast(Iterable[Node], kg.nodes) for qnode_id in cast(Iterable[str], node.qnode_ids)}
    if len([node for node in cast(Iterable[QNode], qg.nodes) if node.id not in qg_ids_hit_by_bindings]) > 0:
        raise ValueError("the node binding list does not cover all nodes in the query graph")

    # --------------------- checking that every KG node is bound to a QG node --------------
    node_ids_of_kg_that_are_not_mapped_to_qg = [node.id for node in cast(Iterable[Node], kg.nodes) if node.id not in node_bindings_map]
    if len(node_ids_of_kg_that_are_not_mapped_to_qg) > 0:
        raise ValueError("KG nodes that are not mapped to QG: " + str(node_ids_of_kg_that_are_not_mapped_to_qg))

    # --------------------- checking that the source ID and target ID of every edge in KG is a valid KG node ---------------------
    node_ids_for_edges_that_are_not_valid_nodes = [edge.source_id for edge in cast(Iterable[Edge], kg.edges) if
                                                   kg_nodes_map.get(edge.source_id, None) is None] +\
        [edge.target_id for edge in cast(Iterable[Edge], kg.edges) if kg_nodes_map.get(edge.target_id, None) is None]
    if len(node_ids_for_edges_that_are_not_valid_nodes) > 0:
        raise ValueError("KG has edges that refer to the following non-existent nodes: " + str(node_ids_for_edges_that_are_not_valid_nodes))

    # --------------------- checking that the source ID and target ID of every edge in QG is a valid QG node ---------------------
    node_ids_for_edges_that_are_not_valid_nodes = [edge.source_id for edge in cast(Iterable[QEdge], qg.edges) if
                                                   qg_nodes_map.get(edge.source_id, None) is None] +\
        [edge.target_id for edge in cast(Iterable[QEdge], qg.edges) if qg_nodes_map.get(edge.target_id, None) is None]
    if len(node_ids_for_edges_that_are_not_valid_nodes) > 0:
        raise ValueError("QG has edges that refer to the following non-existent nodes: " + str(node_ids_for_edges_that_are_not_valid_nodes))

    # --------------------- checking for consistency of edge-to-node relationships, for all edge bindings -----------
    # check that for each bound KG edge, the QG mappings of the KG edges source and target nodes are also the
    # source and target nodes of the QG edge that corresponds to the bound KG edge
    for qedge_id, kg_edge_ids_for_this_qedge_id in kg_edge_ids_by_qedge_id.items():
        qg_edge = next(qedge for qedge in qg.edges if qedge.id == qedge_id)
        qg_source_node_id = qg_edge.source_id
        qg_target_node_id = qg_edge.target_id
        for edge_id in kg_edge_ids_for_this_qedge_id:
            kg_edge = kg_edges_map.get(edge_id)
            kg_source_node_id = kg_edge.source_id
            kg_target_node_id = kg_edge.target_id
            if qg_source_node_id != qg_target_node_id:
                if not ((kg_source_node_id in kg_node_ids_by_qnode_id[qg_source_node_id] and
                         kg_target_node_id in kg_node_ids_by_qnode_id[qg_target_node_id]) or
                        (kg_source_node_id in kg_node_ids_by_qnode_id[qg_target_node_id] and
                         kg_target_node_id in kg_node_ids_by_qnode_id[qg_source_node_id])):
                    kg_source_node = kg_nodes_map.get(kg_source_node_id)
                    kg_target_node = kg_nodes_map.get(kg_target_node_id)
                    raise ValueError(f"Edge {kg_edge.id} (fulfilling {qg_edge.id}) has node(s) that do not fulfill the "
                                     f"expected qnodes ({qg_source_node_id} and {qg_target_node_id}). Edge's nodes are "
                                     f"{kg_source_node_id} (qnode_ids: {kg_source_node.qnode_ids}) and "
                                     f"{kg_target_node_id} (qnode_ids: {kg_target_node.qnode_ids}).")

    # ------- check that for every edge in the QG, any KG nodes that are bound to the QG endpoint nodes of the edge are connected in the KG -------
    for qg_edge in qg_edges_map.values():
        source_id_qg = qg_edge.source_id
        target_id_qg = qg_edge.target_id
        source_node_ids_kg = reverse_node_bindings_map[source_id_qg]
        target_node_ids_kg = reverse_node_bindings_map[target_id_qg]
        # for each source node ID, there should be an edge in KG from this source node to one of the nodes in target_node_ids_kg:
        for source_node_id_kg in source_node_ids_kg:
            if len(kg_node_id_outgoing_adjacency_map[source_node_id_kg] | target_node_ids_kg) == 0:
                raise ValueError("Inconsistent with its binding to the QG, the KG node: " + source_node_id_kg +
                                 " is not connected to *any* of the following nodes: " + str(target_node_ids_kg))
        for target_node_id_kg in target_node_ids_kg:
            if len(kg_node_id_incoming_adjacency_map[target_node_id_kg] | source_node_ids_kg) == 0:
                raise ValueError("Inconsistent with its binding to the QG, the KG node: " + target_node_id_kg +
                                 " is not connected to *any* of the following nodes: " + str(source_node_ids_kg))

    node_types_map = {node.id: node.type for node in cast(Iterable[QNode], qg.nodes)}
    essence_qnode_id = _get_essence_node_for_qg(qg)
    essence_node_type: Optional[BiolinkEntity]
    if essence_qnode_id is not None:
        essence_node_type = node_types_map[essence_qnode_id]
    else:
        essence_node_type = None

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

    kg_node_ids_with_isset_true_dict: Dict[str, Set[str]] = dict()
    kg_node_id_lists_for_qg_nodes = []
    qnode_id_key_list_for_non_set_nodes = []
    # for each node in the query graph:
    for qnode in cast(Iterable[QNode], qg.nodes):
        if qnode.is_set is not None and \
           qnode.is_set and \
           qnode.id not in qg_nodes_override_treat_is_set_as_false:
            kg_node_ids_with_isset_true_dict[qnode.id] = reverse_node_bindings_map[qnode.id]
        else:
            kg_node_id_lists_for_qg_nodes.append(list(reverse_node_bindings_map[qnode.id]))
            qnode_id_key_list_for_non_set_nodes.append(qnode.id)

    results: List[Result] = []

    if len(kg.nodes) == 0:  # issue 692
        return results

    dict_kg = KnowledgeGraph(nodes={node.id: node for node in kg.nodes}, edges={edge.id: edge for edge in kg.edges})

    for node_ids_for_subgraph_from_non_set_nodes in itertools.product(*kg_node_id_lists_for_qg_nodes):
        non_set_node_ids_for_subgraph_dict = dict(zip(qnode_id_key_list_for_non_set_nodes, [{node_id} for node_id in node_ids_for_subgraph_from_non_set_nodes]))
        # Merge the set and non-set node IDs into one dictionary (organized by qnode id)
        node_ids_for_subgraph_by_qnode_id = dict()
        for qnode_id, non_set_node_ids in non_set_node_ids_for_subgraph_dict.items():
            node_ids_for_subgraph_by_qnode_id[qnode_id] = non_set_node_ids
        for qnode_id, kg_node_ids_set in kg_node_ids_with_isset_true_dict.items():
            node_ids_for_subgraph_by_qnode_id[qnode_id] = kg_node_ids_set.copy()  # Important to use a copy!

        # for all KG nodes with isset_true:
        for qg_node_id, kg_node_ids_set in kg_node_ids_with_isset_true_dict.items():
            for kg_node_id in kg_node_ids_set:
                # find all edges of this kg_node_id in the KG
                qg_neighbor_nodes_set = qg_adj_map[qg_node_id]
                # for qg_edge_id in nbhd_qg_edge_ids:
                for qg_neighbor_node_id in qg_neighbor_nodes_set:
                    kg_nodes_for_qg_neighbor_node = reverse_node_bindings_map[qg_neighbor_node_id]
                    found_neighbor_connected_to_kg_node_id = False
                    for kg_neighbor_node_id in kg_nodes_for_qg_neighbor_node:
                        if _make_edge_key(kg_node_id, kg_neighbor_node_id) in kg_undir_edge_keys_set and \
                           kg_neighbor_node_id in node_ids_for_subgraph_by_qnode_id[qg_neighbor_node_id]:
                            found_neighbor_connected_to_kg_node_id = True
                            break
                    if not found_neighbor_connected_to_kg_node_id and kg_node_id in node_ids_for_subgraph_by_qnode_id[qg_node_id]:
                        node_ids_for_subgraph_by_qnode_id[qg_node_id].remove(kg_node_id)
        result = _make_result_from_node_set(dict_kg, node_ids_for_subgraph_by_qnode_id, kg_edge_ids_by_qedge_id, qg)
        # make sure that this set of nodes covers the QG
        qedge_ids_in_subgraph = {qedge_id for kg_edge in cast(KnowledgeGraph, result.result_graph).edges for qedge_id in cast(Iterable[str], kg_edge.qedge_ids) if kg_edge.qedge_ids}
        if len(qedge_ids_set - qedge_ids_in_subgraph) > 0:
            continue
        essence_kg_node_id_set = node_ids_for_subgraph_by_qnode_id.get(essence_qnode_id, set())
        if len(essence_kg_node_id_set) == 1:
            essence_kg_node_id = next(iter(essence_kg_node_id_set))
            essence_kg_node = kg_nodes_map[essence_kg_node_id]
            result.essence = essence_kg_node.name
            if result.essence is None:
                result.essence = essence_kg_node_id
            assert result.essence is not None
            if essence_kg_node.symbol is not None:
                result.essence += " (" + str(essence_kg_node.symbol) + ")"
            result.essence_type = str(essence_node_type)
        elif len(essence_kg_node_id_set) == 0:
            result.essence = cast(str, None)
            result.essence_type = cast(str, None)
        else:
            raise ValueError(f"Result contains more than one node that is a candidate for the essence: {essence_kg_node_id_set}")
        results.append(result)

    # Programmatically generating an informative description for each result
    # seems difficult, but having something non-None is required by the
    # database.  Just put in a placeholder for now, as is done by the
    # QueryGraphReasoner
    for result in results:
        result.description = "No description available"  # see issue 642

    return results
