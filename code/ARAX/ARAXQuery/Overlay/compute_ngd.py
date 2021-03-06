# This class will overlay the normalized google distance on a message (all edges)
#!/bin/env python3
import functools
import json
import math
import subprocess
import sys
import os
import sqlite3
import traceback
import numpy as np
import itertools
from datetime import datetime
from typing import List

# relative imports
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../OpenAPI/python-flask-server/")
from swagger_server.models.edge_attribute import EdgeAttribute
from swagger_server.models.edge import Edge
from swagger_server.models.q_edge import QEdge
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../reasoningtool/kg-construction/")
import NormGoogleDistance
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../NodeSynonymizer/")
from node_synonymizer import NodeSynonymizer


class ComputeNGD:

    #### Constructor
    def __init__(self, response, message, parameters):
        self.response = response
        self.message = message
        self.parameters = parameters
        self.global_iter = 0
        self.ngd_database_name = "curie_to_pmids.sqlite"
        self.connection, self.cursor = self._setup_ngd_database()
        self.curie_to_pmids_map = dict()
        self.ngd_normalizer = 2.2e+7 * 20  # From PubMed home page there are 27 million articles; avg 20 MeSH terms per article
        self.NGD = NormGoogleDistance.NormGoogleDistance()  # should I be importing here, or before the class? Feel like Eric said avoid global vars...

    def compute_ngd(self):
        """
        Iterate over all the edges in the knowledge graph, compute the normalized google distance and stick that info
        on the edge_attributes
        :default: The default value to set for NGD if it returns a nan
        :return: response
        """
        if self.response.status != 'OK':  # Catches any errors that may have been logged during initialization
            self._close_database()
            return self.response
        parameters = self.parameters
        self.response.debug(f"Computing NGD")
        self.response.info(f"Computing the normalized Google distance: weighting edges based on source/target node "
                           f"co-occurrence frequency in PubMed abstracts")

        self.response.info("Converting CURIE identifiers to human readable names")
        node_curie_to_name = dict()
        try:
            for node in self.message.knowledge_graph.nodes:
                node_curie_to_name[node.id] = node.name
        except:
            tb = traceback.format_exc()
            error_type, error, _ = sys.exc_info()
            self.response.error(f"Something went wrong when converting names")
            self.response.error(tb, error_code=error_type.__name__)

        name = "normalized_google_distance"
        type = "EDAM:data_2526"
        value = self.parameters['default_value']
        url = "https://arax.rtx.ai/api/rtx/v1/ui/#/PubmedMeshNgd"

        # if you want to add virtual edges, identify the source/targets, decorate the edges, add them to the KG, and then add one to the QG corresponding to them
        if 'virtual_relation_label' in parameters:
            source_curies_to_decorate = set()
            target_curies_to_decorate = set()
            curies_to_names = dict()
            # identify the nodes that we should be adding virtual edges for
            for node in self.message.knowledge_graph.nodes:
                if hasattr(node, 'qnode_ids'):
                    if parameters['source_qnode_id'] in node.qnode_ids:
                        source_curies_to_decorate.add(node.id)
                        curies_to_names[node.id] = node.name
                    if parameters['target_qnode_id'] in node.qnode_ids:
                        target_curies_to_decorate.add(node.id)
                        curies_to_names[node.id] = node.name

            # Convert these curies to their canonicalized curies (needed for the local NGD system)
            canonicalized_curie_map = self._get_canonical_curies_map(list(source_curies_to_decorate.union(target_curies_to_decorate)))
            self.load_curie_to_pmids_data(canonicalized_curie_map.values())
            added_flag = False  # check to see if any edges where added
            num_computed_total = 0
            num_computed_slow = 0
            self.response.debug(f"Looping through node pairs and calculating NGD values")
            # iterate over all pairs of these nodes, add the virtual edge, decorate with the correct attribute
            for (source_curie, target_curie) in itertools.product(source_curies_to_decorate, target_curies_to_decorate):
                # create the edge attribute if it can be
                source_name = curies_to_names[source_curie]
                target_name = curies_to_names[target_curie]
                num_computed_total += 1
                canonical_source_curie = canonicalized_curie_map.get(source_curie, source_curie)
                canonical_target_curie = canonicalized_curie_map.get(target_curie, target_curie)
                ngd_value = self.calculate_ngd_fast(canonical_source_curie, canonical_target_curie)
                if ngd_value is None:
                    ngd_value = self.NGD.get_ngd_for_all([source_curie, target_curie], [source_name, target_name])
                    self.response.debug(f"Had to use eUtils to compute NGD between {source_name} "
                                        f"({canonical_source_curie}) and {target_name} ({canonical_target_curie}). "
                                        f"Value is: {ngd_value}")
                    num_computed_slow += 1
                if np.isfinite(ngd_value):  # if ngd is finite, that's ok, otherwise, stay with default
                    value = ngd_value
                edge_attribute = EdgeAttribute(type=type, name=name, value=str(value), url=url)  # populate the NGD edge attribute
                if edge_attribute:
                    added_flag = True
                    # make the edge, add the attribute

                    # edge properties
                    now = datetime.now()
                    edge_type = "has_normalized_google_distance_with"
                    qedge_ids = [parameters['virtual_relation_label']]
                    relation = parameters['virtual_relation_label']
                    is_defined_by = "ARAX"
                    defined_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
                    provided_by = "ARAX"
                    confidence = None
                    weight = None  # TODO: could make the actual value of the attribute
                    source_id = source_curie
                    target_id = target_curie

                    # now actually add the virtual edges in
                    id = f"{relation}_{self.global_iter}"
                    self.global_iter += 1
                    edge = Edge(id=id, type=edge_type, relation=relation, source_id=source_id,
                                target_id=target_id,
                                is_defined_by=is_defined_by, defined_datetime=defined_datetime,
                                provided_by=provided_by,
                                confidence=confidence, weight=weight, edge_attributes=[edge_attribute], qedge_ids=qedge_ids)
                    self.message.knowledge_graph.edges.append(edge)

            # Now add a q_edge the query_graph since I've added an extra edge to the KG
            if added_flag:
                #edge_type = parameters['virtual_edge_type']
                edge_type = "has_normalized_google_distance_with"
                relation = parameters['virtual_relation_label']
                q_edge = QEdge(id=relation, type=edge_type, relation=relation,
                               source_id=parameters['source_qnode_id'], target_id=parameters[
                        'target_qnode_id'])
                self.message.query_graph.edges.append(q_edge)

            self.response.info(f"NGD values successfully added to edges")
            num_computed_fast = num_computed_total - num_computed_slow
            percent_computed_fast = round((num_computed_fast / num_computed_total) * 100)
            self.response.debug(f"Used fastNGD for {percent_computed_fast}% of edges "
                                f"({num_computed_fast} of {num_computed_total})")
        else:  # you want to add it for each edge in the KG
            # iterate over KG edges, add the information
            try:
                # Map all nodes to their canonicalized curies in one batch (need canonical IDs for the local NGD system)
                canonicalized_curie_map = self._get_canonical_curies_map([node.id for node in self.message.knowledge_graph.nodes])
                self.load_curie_to_pmids_data(canonicalized_curie_map.values())
                num_computed_total = 0
                num_computed_slow = 0
                self.response.debug(f"Looping through edges and calculating NGD values")
                for edge in self.message.knowledge_graph.edges:
                    # Make sure the edge_attributes are not None
                    if not edge.edge_attributes:
                        edge.edge_attributes = []  # should be an array, but why not a list?
                    # now go and actually get the NGD
                    source_curie = edge.source_id
                    target_curie = edge.target_id
                    source_name = node_curie_to_name[source_curie]
                    target_name = node_curie_to_name[target_curie]
                    num_computed_total += 1
                    canonical_source_curie = canonicalized_curie_map.get(source_curie, source_curie)
                    canonical_target_curie = canonicalized_curie_map.get(target_curie, target_curie)
                    ngd_value = self.calculate_ngd_fast(canonical_source_curie, canonical_target_curie)
                    if ngd_value is None:
                        ngd_value = self.NGD.get_ngd_for_all([source_curie, target_curie], [source_name, target_name])
                        self.response.debug(f"Had to use eUtils to compute NGD between {source_name} "
                                            f"({canonical_source_curie}) and {target_name} ({canonical_target_curie}). "
                                            f"Value is: {ngd_value}")
                        num_computed_slow += 1
                    if np.isfinite(ngd_value):  # if ngd is finite, that's ok, otherwise, stay with default
                        value = ngd_value
                    ngd_edge_attribute = EdgeAttribute(type=type, name=name, value=str(value), url=url)  # populate the NGD edge attribute
                    edge.edge_attributes.append(ngd_edge_attribute)  # append it to the list of attributes
            except:
                tb = traceback.format_exc()
                error_type, error, _ = sys.exc_info()
                self.response.error(tb, error_code=error_type.__name__)
                self.response.error(f"Something went wrong adding the NGD edge attributes")
            else:
                self.response.info(f"NGD values successfully added to edges")
                num_computed_fast = num_computed_total - num_computed_slow
                percent_computed_fast = round((num_computed_fast / num_computed_total) * 100)
                self.response.debug(f"Used fastNGD for {percent_computed_fast}% of edges "
                                    f"({num_computed_fast} of {num_computed_total})")
            self._close_database()
            return self.response

    def load_curie_to_pmids_data(self, canonicalized_curies):
        self.response.debug(f"Extracting PMID lists from sqlite database for relevant nodes")
        curies = list(set(canonicalized_curies))
        chunk_size = 20000
        num_chunks = len(curies) // chunk_size if len(curies) % chunk_size == 0 else (len(curies) // chunk_size) + 1
        start_index = 0
        stop_index = chunk_size
        for num in range(num_chunks):
            chunk = curies[start_index:stop_index] if stop_index <= len(curies) else curies[start_index:]
            curie_list_str = ", ".join([f"'{curie}'" for curie in chunk])
            self.cursor.execute(f"SELECT * FROM curie_to_pmids WHERE curie in ({curie_list_str})")
            rows = self.cursor.fetchall()
            for row in rows:
                self.curie_to_pmids_map[row[0]] = json.loads(row[1])  # PMID list is stored as JSON string in sqlite db
            start_index += chunk_size
            stop_index += chunk_size

    def calculate_ngd_fast(self, source_curie, target_curie):
        if source_curie in self.curie_to_pmids_map and target_curie in self.curie_to_pmids_map:
            pubmed_ids_for_curies = [self.curie_to_pmids_map.get(source_curie),
                                     self.curie_to_pmids_map.get(target_curie)]
            counts_res = self._compute_marginal_and_joint_counts(pubmed_ids_for_curies)
            return self._compute_multiway_ngd_from_counts(*counts_res)
        else:
            return None

    @staticmethod
    def _compute_marginal_and_joint_counts(concept_pubmed_ids: List[List[int]]) -> list:
        return [list(map(lambda pmid_list: len(set(pmid_list)), concept_pubmed_ids)),
                len(functools.reduce(lambda pmids_intersec_cumul, pmids_next:
                                     set(pmids_next).intersection(pmids_intersec_cumul),
                                     concept_pubmed_ids))]

    def _compute_multiway_ngd_from_counts(self, marginal_counts: List[int],
                                          joint_count: int) -> float:
        # Make sure that things are within the right domain for the logs
        # Should also make sure things are not negative, but I'll just do this with a ValueError
        if None in marginal_counts:
            return math.nan
        elif 0 in marginal_counts or 0. in marginal_counts:
            return math.nan
        elif joint_count == 0 or joint_count == 0.:
            return math.nan
        else:
            try:
                return (max([math.log(count) for count in marginal_counts]) - math.log(joint_count)) / \
                   (math.log(self.ngd_normalizer) - min([math.log(count) for count in marginal_counts]))
            except ValueError:
                return math.nan

    def _get_canonical_curies_map(self, curies):
        self.response.debug(f"Canonicalizing curies of relevant nodes using NodeSynonymizer")
        synonymizer = NodeSynonymizer()
        try:
            canonicalized_node_info = synonymizer.get_canonical_curies(curies)
        except Exception:
            tb = traceback.format_exc()
            error_type, error, _ = sys.exc_info()
            self.response.error(f"Encountered a problem using NodeSynonymizer: {tb}", error_code=error_type.__name__)
            return {}
        else:
            canonical_curies_map = dict()
            for input_curie, node_info in canonicalized_node_info.items():
                if node_info:
                    canonical_curies_map[input_curie] = node_info.get('preferred_curie', input_curie)
                else:
                    canonical_curies_map[input_curie] = input_curie
            return canonical_curies_map

    def _setup_ngd_database(self):
        # Download the ngd database if there isn't already a local copy or if a newer version is available
        db_path_local = f"{os.path.dirname(os.path.abspath(__file__))}/ngd/{self.ngd_database_name}"
        db_path_remote = f"/home/ubuntu/databases_for_download/{self.ngd_database_name}"
        if not os.path.exists(f"{db_path_local}"):
            self.response.debug(f"Downloading fast NGD database because no copy exists... (will take a few minutes)")
            os.system(f"scp rtxconfig@arax.rtx.ai:{db_path_remote} {db_path_local}")
        else:
            last_modified_local = int(os.path.getmtime(db_path_local))
            last_modified_remote_byte_str = subprocess.check_output(f"ssh rtxconfig@arax.rtx.ai 'stat -c %Y {db_path_remote}'", shell=True)
            last_modified_remote = int(str(last_modified_remote_byte_str, 'utf-8'))
            if last_modified_local < last_modified_remote:
                self.response.debug(f"Downloading new version of fast NGD database... (will take a few minutes)")
                os.system(f"scp rtxconfig@arax.rtx.ai:{db_path_remote} {db_path_local}")
            else:
                self.response.debug(f"Confirmed local NGD database is current")
        # Set up a connection to the database so it's ready for use
        try:
            connection = sqlite3.connect(db_path_local)
            cursor = connection.cursor()
        except Exception:
            self.response.error(f"Encountered an error connecting to ngd sqlite database", error_code="DatabaseSetupIssue")
            return None, None
        else:
            return connection, cursor

    def _close_database(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
