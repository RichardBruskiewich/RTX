# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server.models.knowledge_graph import KnowledgeGraph  # noqa: F401,E501
from swagger_server import util


class Result(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, id: str=None, description: str=None, essence: str=None, essence_type: str=None, row_data: List[str]=None, score: float=None, score_name: str=None, score_direction: str=None, confidence: float=None, result_type: str=None, result_group: int=None, result_group_similarity_score: float=None, reasoner_id: str=None, result_graph: KnowledgeGraph=None, node_bindings: object=None, edge_bindings: object=None):  # noqa: E501
        """Result - a model defined in Swagger

        :param id: The id of this Result.  # noqa: E501
        :type id: str
        :param description: The description of this Result.  # noqa: E501
        :type description: str
        :param essence: The essence of this Result.  # noqa: E501
        :type essence: str
        :param essence_type: The essence_type of this Result.  # noqa: E501
        :type essence_type: str
        :param row_data: The row_data of this Result.  # noqa: E501
        :type row_data: List[str]
        :param score: The score of this Result.  # noqa: E501
        :type score: float
        :param score_name: The score_name of this Result.  # noqa: E501
        :type score_name: str
        :param score_direction: The score_direction of this Result.  # noqa: E501
        :type score_direction: str
        :param confidence: The confidence of this Result.  # noqa: E501
        :type confidence: float
        :param result_type: The result_type of this Result.  # noqa: E501
        :type result_type: str
        :param result_group: The result_group of this Result.  # noqa: E501
        :type result_group: int
        :param result_group_similarity_score: The result_group_similarity_score of this Result.  # noqa: E501
        :type result_group_similarity_score: float
        :param reasoner_id: The reasoner_id of this Result.  # noqa: E501
        :type reasoner_id: str
        :param result_graph: The result_graph of this Result.  # noqa: E501
        :type result_graph: KnowledgeGraph
        :param node_bindings: The node_bindings of this Result.  # noqa: E501
        :type node_bindings: object
        :param edge_bindings: The edge_bindings of this Result.  # noqa: E501
        :type edge_bindings: object
        """
        self.swagger_types = {
            'id': str,
            'description': str,
            'essence': str,
            'essence_type': str,
            'row_data': List[str],
            'score': float,
            'score_name': str,
            'score_direction': str,
            'confidence': float,
            'result_type': str,
            'result_group': int,
            'result_group_similarity_score': float,
            'reasoner_id': str,
            'result_graph': KnowledgeGraph,
            'node_bindings': object,
            'edge_bindings': object
        }

        self.attribute_map = {
            'id': 'id',
            'description': 'description',
            'essence': 'essence',
            'essence_type': 'essence_type',
            'row_data': 'row_data',
            'score': 'score',
            'score_name': 'score_name',
            'score_direction': 'score_direction',
            'confidence': 'confidence',
            'result_type': 'result_type',
            'result_group': 'result_group',
            'result_group_similarity_score': 'result_group_similarity_score',
            'reasoner_id': 'reasoner_id',
            'result_graph': 'result_graph',
            'node_bindings': 'node_bindings',
            'edge_bindings': 'edge_bindings'
        }

        self._id = id
        self._description = description
        self._essence = essence
        self._essence_type = essence_type
        self._row_data = row_data
        self._score = score
        self._score_name = score_name
        self._score_direction = score_direction
        self._confidence = confidence
        self._result_type = result_type
        self._result_group = result_group
        self._result_group_similarity_score = result_group_similarity_score
        self._reasoner_id = reasoner_id
        self._result_graph = result_graph
        self._node_bindings = node_bindings
        self._edge_bindings = edge_bindings

    @classmethod
    def from_dict(cls, dikt) -> 'Result':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Result of this Result.  # noqa: E501
        :rtype: Result
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self) -> str:
        """Gets the id of this Result.

        URI for this message  # noqa: E501

        :return: The id of this Result.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id: str):
        """Sets the id of this Result.

        URI for this message  # noqa: E501

        :param id: The id of this Result.
        :type id: str
        """

        self._id = id

    @property
    def description(self) -> str:
        """Gets the description of this Result.

        A free text description of this result answer from the reasoner  # noqa: E501

        :return: The description of this Result.
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description: str):
        """Sets the description of this Result.

        A free text description of this result answer from the reasoner  # noqa: E501

        :param description: The description of this Result.
        :type description: str
        """

        self._description = description

    @property
    def essence(self) -> str:
        """Gets the essence of this Result.

        A single string that is the terse essence of the result (useful for simple answers)  # noqa: E501

        :return: The essence of this Result.
        :rtype: str
        """
        return self._essence

    @essence.setter
    def essence(self, essence: str):
        """Sets the essence of this Result.

        A single string that is the terse essence of the result (useful for simple answers)  # noqa: E501

        :param essence: The essence of this Result.
        :type essence: str
        """

        self._essence = essence

    @property
    def essence_type(self) -> str:
        """Gets the essence_type of this Result.

        A Translator bioentity type of the essence  # noqa: E501

        :return: The essence_type of this Result.
        :rtype: str
        """
        return self._essence_type

    @essence_type.setter
    def essence_type(self, essence_type: str):
        """Sets the essence_type of this Result.

        A Translator bioentity type of the essence  # noqa: E501

        :param essence_type: The essence_type of this Result.
        :type essence_type: str
        """

        self._essence_type = essence_type

    @property
    def row_data(self) -> List[str]:
        """Gets the row_data of this Result.

        An arbitrary list of values that captures the essence of the result that can be turned into a tabular result across all answers (each result is a row) for a user that wants tabular output  # noqa: E501

        :return: The row_data of this Result.
        :rtype: List[str]
        """
        return self._row_data

    @row_data.setter
    def row_data(self, row_data: List[str]):
        """Sets the row_data of this Result.

        An arbitrary list of values that captures the essence of the result that can be turned into a tabular result across all answers (each result is a row) for a user that wants tabular output  # noqa: E501

        :param row_data: The row_data of this Result.
        :type row_data: List[str]
        """

        self._row_data = row_data

    @property
    def score(self) -> float:
        """Gets the score of this Result.

        Any type of score associated with this result  # noqa: E501

        :return: The score of this Result.
        :rtype: float
        """
        return self._score

    @score.setter
    def score(self, score: float):
        """Sets the score of this Result.

        Any type of score associated with this result  # noqa: E501

        :param score: The score of this Result.
        :type score: float
        """

        self._score = score

    @property
    def score_name(self) -> str:
        """Gets the score_name of this Result.

        Name for the score  # noqa: E501

        :return: The score_name of this Result.
        :rtype: str
        """
        return self._score_name

    @score_name.setter
    def score_name(self, score_name: str):
        """Sets the score_name of this Result.

        Name for the score  # noqa: E501

        :param score_name: The score_name of this Result.
        :type score_name: str
        """

        self._score_name = score_name

    @property
    def score_direction(self) -> str:
        """Gets the score_direction of this Result.

        Sorting indicator for the score: one of higher_is_better or lower_is_better  # noqa: E501

        :return: The score_direction of this Result.
        :rtype: str
        """
        return self._score_direction

    @score_direction.setter
    def score_direction(self, score_direction: str):
        """Sets the score_direction of this Result.

        Sorting indicator for the score: one of higher_is_better or lower_is_better  # noqa: E501

        :param score_direction: The score_direction of this Result.
        :type score_direction: str
        """

        self._score_direction = score_direction

    @property
    def confidence(self) -> float:
        """Gets the confidence of this Result.

        Confidence metric for this result, a value between (inclusive) 0.0 (no confidence) and 1.0 (highest confidence)  # noqa: E501

        :return: The confidence of this Result.
        :rtype: float
        """
        return self._confidence

    @confidence.setter
    def confidence(self, confidence: float):
        """Sets the confidence of this Result.

        Confidence metric for this result, a value between (inclusive) 0.0 (no confidence) and 1.0 (highest confidence)  # noqa: E501

        :param confidence: The confidence of this Result.
        :type confidence: float
        """

        self._confidence = confidence

    @property
    def result_type(self) -> str:
        """Gets the result_type of this Result.

        One of several possible result types: 'individual query answer', 'neighborhood graph', 'type summary graph'  # noqa: E501

        :return: The result_type of this Result.
        :rtype: str
        """
        return self._result_type

    @result_type.setter
    def result_type(self, result_type: str):
        """Sets the result_type of this Result.

        One of several possible result types: 'individual query answer', 'neighborhood graph', 'type summary graph'  # noqa: E501

        :param result_type: The result_type of this Result.
        :type result_type: str
        """

        self._result_type = result_type

    @property
    def result_group(self) -> int:
        """Gets the result_group of this Result.

        An integer group number for results for use in cases where several results should be grouped together. Also useful to control sorting ascending.  # noqa: E501

        :return: The result_group of this Result.
        :rtype: int
        """
        return self._result_group

    @result_group.setter
    def result_group(self, result_group: int):
        """Sets the result_group of this Result.

        An integer group number for results for use in cases where several results should be grouped together. Also useful to control sorting ascending.  # noqa: E501

        :param result_group: The result_group of this Result.
        :type result_group: int
        """

        self._result_group = result_group

    @property
    def result_group_similarity_score(self) -> float:
        """Gets the result_group_similarity_score of this Result.

        A score that denotes the similarity of this result to other members of the result_group  # noqa: E501

        :return: The result_group_similarity_score of this Result.
        :rtype: float
        """
        return self._result_group_similarity_score

    @result_group_similarity_score.setter
    def result_group_similarity_score(self, result_group_similarity_score: float):
        """Sets the result_group_similarity_score of this Result.

        A score that denotes the similarity of this result to other members of the result_group  # noqa: E501

        :param result_group_similarity_score: The result_group_similarity_score of this Result.
        :type result_group_similarity_score: float
        """

        self._result_group_similarity_score = result_group_similarity_score

    @property
    def reasoner_id(self) -> str:
        """Gets the reasoner_id of this Result.

        Identifier string of the reasoner that provided this result (e.g., RTX, Robokop, Indigo, Integrator)  # noqa: E501

        :return: The reasoner_id of this Result.
        :rtype: str
        """
        return self._reasoner_id

    @reasoner_id.setter
    def reasoner_id(self, reasoner_id: str):
        """Sets the reasoner_id of this Result.

        Identifier string of the reasoner that provided this result (e.g., RTX, Robokop, Indigo, Integrator)  # noqa: E501

        :param reasoner_id: The reasoner_id of this Result.
        :type reasoner_id: str
        """

        self._reasoner_id = reasoner_id

    @property
    def result_graph(self) -> KnowledgeGraph:
        """Gets the result_graph of this Result.

        A graph that describes the thought pattern of this result (i.e. answer to the query)  # noqa: E501

        :return: The result_graph of this Result.
        :rtype: KnowledgeGraph
        """
        return self._result_graph

    @result_graph.setter
    def result_graph(self, result_graph: KnowledgeGraph):
        """Sets the result_graph of this Result.

        A graph that describes the thought pattern of this result (i.e. answer to the query)  # noqa: E501

        :param result_graph: The result_graph of this Result.
        :type result_graph: KnowledgeGraph
        """

        self._result_graph = result_graph

    @property
    def node_bindings(self) -> object:
        """Gets the node_bindings of this Result.

        Lookup dict that maps QNode identifiers in the QueryGraph to Node identifiers in the KnowledgeGraph  # noqa: E501

        :return: The node_bindings of this Result.
        :rtype: object
        """
        return self._node_bindings

    @node_bindings.setter
    def node_bindings(self, node_bindings: object):
        """Sets the node_bindings of this Result.

        Lookup dict that maps QNode identifiers in the QueryGraph to Node identifiers in the KnowledgeGraph  # noqa: E501

        :param node_bindings: The node_bindings of this Result.
        :type node_bindings: object
        """

        self._node_bindings = node_bindings

    @property
    def edge_bindings(self) -> object:
        """Gets the edge_bindings of this Result.

        Lookup dict that maps QEdge identifiers in the QueryGraph to Edge identifiers in the KnowledgeGraph  # noqa: E501

        :return: The edge_bindings of this Result.
        :rtype: object
        """
        return self._edge_bindings

    @edge_bindings.setter
    def edge_bindings(self, edge_bindings: object):
        """Sets the edge_bindings of this Result.

        Lookup dict that maps QEdge identifiers in the QueryGraph to Edge identifiers in the KnowledgeGraph  # noqa: E501

        :param edge_bindings: The edge_bindings of this Result.
        :type edge_bindings: object
        """

        self._edge_bindings = edge_bindings
