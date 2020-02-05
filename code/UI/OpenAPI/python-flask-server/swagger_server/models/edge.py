# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server.models.biolink_relation import BiolinkRelation  # noqa: F401,E501
from swagger_server.models.edge_attribute import EdgeAttribute  # noqa: F401,E501
from swagger_server import util


class Edge(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, id: str=None, type: BiolinkRelation=None, relation: str=None, source_id: str=None, target_id: str=None, is_defined_by: str=None, defined_datetime: str=None, provided_by: str=None, confidence: float=None, weight: float=None, publications: List[str]=None, evidence_type: str=None, qualifiers: str=None, negated: bool=None, edge_attributes: List[EdgeAttribute]=None, qedge_id: str=None):  # noqa: E501
        """Edge - a model defined in Swagger

        :param id: The id of this Edge.  # noqa: E501
        :type id: str
        :param type: The type of this Edge.  # noqa: E501
        :type type: BiolinkRelation
        :param relation: The relation of this Edge.  # noqa: E501
        :type relation: str
        :param source_id: The source_id of this Edge.  # noqa: E501
        :type source_id: str
        :param target_id: The target_id of this Edge.  # noqa: E501
        :type target_id: str
        :param is_defined_by: The is_defined_by of this Edge.  # noqa: E501
        :type is_defined_by: str
        :param defined_datetime: The defined_datetime of this Edge.  # noqa: E501
        :type defined_datetime: str
        :param provided_by: The provided_by of this Edge.  # noqa: E501
        :type provided_by: str
        :param confidence: The confidence of this Edge.  # noqa: E501
        :type confidence: float
        :param weight: The weight of this Edge.  # noqa: E501
        :type weight: float
        :param publications: The publications of this Edge.  # noqa: E501
        :type publications: List[str]
        :param evidence_type: The evidence_type of this Edge.  # noqa: E501
        :type evidence_type: str
        :param qualifiers: The qualifiers of this Edge.  # noqa: E501
        :type qualifiers: str
        :param negated: The negated of this Edge.  # noqa: E501
        :type negated: bool
        :param edge_attributes: The edge_attributes of this Edge.  # noqa: E501
        :type edge_attributes: List[EdgeAttribute]
        :param qedge_id: The qedge_id of this Edge.  # noqa: E501
        :type qedge_id: str
        """
        self.swagger_types = {
            'id': str,
            'type': BiolinkRelation,
            'relation': str,
            'source_id': str,
            'target_id': str,
            'is_defined_by': str,
            'defined_datetime': str,
            'provided_by': str,
            'confidence': float,
            'weight': float,
            'publications': List[str],
            'evidence_type': str,
            'qualifiers': str,
            'negated': bool,
            'edge_attributes': List[EdgeAttribute],
            'qedge_id': str
        }

        self.attribute_map = {
            'id': 'id',
            'type': 'type',
            'relation': 'relation',
            'source_id': 'source_id',
            'target_id': 'target_id',
            'is_defined_by': 'is_defined_by',
            'defined_datetime': 'defined_datetime',
            'provided_by': 'provided_by',
            'confidence': 'confidence',
            'weight': 'weight',
            'publications': 'publications',
            'evidence_type': 'evidence_type',
            'qualifiers': 'qualifiers',
            'negated': 'negated',
            'edge_attributes': 'edge_attributes',
            'qedge_id': 'qedge_id'
        }

        self._id = id
        self._type = type
        self._relation = relation
        self._source_id = source_id
        self._target_id = target_id
        self._is_defined_by = is_defined_by
        self._defined_datetime = defined_datetime
        self._provided_by = provided_by
        self._confidence = confidence
        self._weight = weight
        self._publications = publications
        self._evidence_type = evidence_type
        self._qualifiers = qualifiers
        self._negated = negated
        self._edge_attributes = edge_attributes
        self._qedge_id = qedge_id

    @classmethod
    def from_dict(cls, dikt) -> 'Edge':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The Edge of this Edge.  # noqa: E501
        :rtype: Edge
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self) -> str:
        """Gets the id of this Edge.

        Local identifier for this node which is unique within this KnowledgeGraph, and perhaps within the source reasoner's knowledge graph  # noqa: E501

        :return: The id of this Edge.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id: str):
        """Sets the id of this Edge.

        Local identifier for this node which is unique within this KnowledgeGraph, and perhaps within the source reasoner's knowledge graph  # noqa: E501

        :param id: The id of this Edge.
        :type id: str
        """
        if id is None:
            raise ValueError("Invalid value for `id`, must not be `None`")  # noqa: E501

        self._id = id

    @property
    def type(self) -> BiolinkRelation:
        """Gets the type of this Edge.


        :return: The type of this Edge.
        :rtype: BiolinkRelation
        """
        return self._type

    @type.setter
    def type(self, type: BiolinkRelation):
        """Sets the type of this Edge.


        :param type: The type of this Edge.
        :type type: BiolinkRelation
        """

        self._type = type

    @property
    def relation(self) -> str:
        """Gets the relation of this Edge.

        Lower-level relationship type of this edge  # noqa: E501

        :return: The relation of this Edge.
        :rtype: str
        """
        return self._relation

    @relation.setter
    def relation(self, relation: str):
        """Sets the relation of this Edge.

        Lower-level relationship type of this edge  # noqa: E501

        :param relation: The relation of this Edge.
        :type relation: str
        """

        self._relation = relation

    @property
    def source_id(self) -> str:
        """Gets the source_id of this Edge.

        Corresponds to the @id of source node of this edge  # noqa: E501

        :return: The source_id of this Edge.
        :rtype: str
        """
        return self._source_id

    @source_id.setter
    def source_id(self, source_id: str):
        """Sets the source_id of this Edge.

        Corresponds to the @id of source node of this edge  # noqa: E501

        :param source_id: The source_id of this Edge.
        :type source_id: str
        """
        if source_id is None:
            raise ValueError("Invalid value for `source_id`, must not be `None`")  # noqa: E501

        self._source_id = source_id

    @property
    def target_id(self) -> str:
        """Gets the target_id of this Edge.

        Corresponds to the @id of target node of this edge  # noqa: E501

        :return: The target_id of this Edge.
        :rtype: str
        """
        return self._target_id

    @target_id.setter
    def target_id(self, target_id: str):
        """Sets the target_id of this Edge.

        Corresponds to the @id of target node of this edge  # noqa: E501

        :param target_id: The target_id of this Edge.
        :type target_id: str
        """
        if target_id is None:
            raise ValueError("Invalid value for `target_id`, must not be `None`")  # noqa: E501

        self._target_id = target_id

    @property
    def is_defined_by(self) -> str:
        """Gets the is_defined_by of this Edge.

        A CURIE/URI for the translator group that made the KG  # noqa: E501

        :return: The is_defined_by of this Edge.
        :rtype: str
        """
        return self._is_defined_by

    @is_defined_by.setter
    def is_defined_by(self, is_defined_by: str):
        """Sets the is_defined_by of this Edge.

        A CURIE/URI for the translator group that made the KG  # noqa: E501

        :param is_defined_by: The is_defined_by of this Edge.
        :type is_defined_by: str
        """

        self._is_defined_by = is_defined_by

    @property
    def defined_datetime(self) -> str:
        """Gets the defined_datetime of this Edge.

        Datetime at which the KG builder/updater pulled the information from the original source. Used as a freshness indicator.  # noqa: E501

        :return: The defined_datetime of this Edge.
        :rtype: str
        """
        return self._defined_datetime

    @defined_datetime.setter
    def defined_datetime(self, defined_datetime: str):
        """Sets the defined_datetime of this Edge.

        Datetime at which the KG builder/updater pulled the information from the original source. Used as a freshness indicator.  # noqa: E501

        :param defined_datetime: The defined_datetime of this Edge.
        :type defined_datetime: str
        """

        self._defined_datetime = defined_datetime

    @property
    def provided_by(self) -> str:
        """Gets the provided_by of this Edge.

        A CURIE/URI for the knowledge source that defined this edge  # noqa: E501

        :return: The provided_by of this Edge.
        :rtype: str
        """
        return self._provided_by

    @provided_by.setter
    def provided_by(self, provided_by: str):
        """Sets the provided_by of this Edge.

        A CURIE/URI for the knowledge source that defined this edge  # noqa: E501

        :param provided_by: The provided_by of this Edge.
        :type provided_by: str
        """

        self._provided_by = provided_by

    @property
    def confidence(self) -> float:
        """Gets the confidence of this Edge.

        Confidence metric for this edge, a value between (inclusive) 0.0 (no confidence) and 1.0 (highest confidence)  # noqa: E501

        :return: The confidence of this Edge.
        :rtype: float
        """
        return self._confidence

    @confidence.setter
    def confidence(self, confidence: float):
        """Sets the confidence of this Edge.

        Confidence metric for this edge, a value between (inclusive) 0.0 (no confidence) and 1.0 (highest confidence)  # noqa: E501

        :param confidence: The confidence of this Edge.
        :type confidence: float
        """

        self._confidence = confidence

    @property
    def weight(self) -> float:
        """Gets the weight of this Edge.

        Weight metric for this edge, with no upper bound. Perhaps useful when formal confidence metrics are not available  # noqa: E501

        :return: The weight of this Edge.
        :rtype: float
        """
        return self._weight

    @weight.setter
    def weight(self, weight: float):
        """Sets the weight of this Edge.

        Weight metric for this edge, with no upper bound. Perhaps useful when formal confidence metrics are not available  # noqa: E501

        :param weight: The weight of this Edge.
        :type weight: float
        """

        self._weight = weight

    @property
    def publications(self) -> List[str]:
        """Gets the publications of this Edge.

        List of CURIEs for publications associated with this edge  # noqa: E501

        :return: The publications of this Edge.
        :rtype: List[str]
        """
        return self._publications

    @publications.setter
    def publications(self, publications: List[str]):
        """Sets the publications of this Edge.

        List of CURIEs for publications associated with this edge  # noqa: E501

        :param publications: The publications of this Edge.
        :type publications: List[str]
        """

        self._publications = publications

    @property
    def evidence_type(self) -> str:
        """Gets the evidence_type of this Edge.

        A CURIE/URI for class of evidence supporting the statement made in an edge - typically a class from the ECO ontology  # noqa: E501

        :return: The evidence_type of this Edge.
        :rtype: str
        """
        return self._evidence_type

    @evidence_type.setter
    def evidence_type(self, evidence_type: str):
        """Sets the evidence_type of this Edge.

        A CURIE/URI for class of evidence supporting the statement made in an edge - typically a class from the ECO ontology  # noqa: E501

        :param evidence_type: The evidence_type of this Edge.
        :type evidence_type: str
        """

        self._evidence_type = evidence_type

    @property
    def qualifiers(self) -> str:
        """Gets the qualifiers of this Edge.

        Terms representing qualifiers that modify or qualify the meaning of the statement made in an edge  # noqa: E501

        :return: The qualifiers of this Edge.
        :rtype: str
        """
        return self._qualifiers

    @qualifiers.setter
    def qualifiers(self, qualifiers: str):
        """Sets the qualifiers of this Edge.

        Terms representing qualifiers that modify or qualify the meaning of the statement made in an edge  # noqa: E501

        :param qualifiers: The qualifiers of this Edge.
        :type qualifiers: str
        """

        self._qualifiers = qualifiers

    @property
    def negated(self) -> bool:
        """Gets the negated of this Edge.

        Boolean that if set to true, indicates the edge statement is negated i.e. is not true  # noqa: E501

        :return: The negated of this Edge.
        :rtype: bool
        """
        return self._negated

    @negated.setter
    def negated(self, negated: bool):
        """Sets the negated of this Edge.

        Boolean that if set to true, indicates the edge statement is negated i.e. is not true  # noqa: E501

        :param negated: The negated of this Edge.
        :type negated: bool
        """

        self._negated = negated

    @property
    def edge_attributes(self) -> List[EdgeAttribute]:
        """Gets the edge_attributes of this Edge.

        A list of additional attributes for this edge  # noqa: E501

        :return: The edge_attributes of this Edge.
        :rtype: List[EdgeAttribute]
        """
        return self._edge_attributes

    @edge_attributes.setter
    def edge_attributes(self, edge_attributes: List[EdgeAttribute]):
        """Sets the edge_attributes of this Edge.

        A list of additional attributes for this edge  # noqa: E501

        :param edge_attributes: The edge_attributes of this Edge.
        :type edge_attributes: List[EdgeAttribute]
        """

        self._edge_attributes = edge_attributes

    @property
    def qedge_id(self) -> str:
        """Gets the qedge_id of this Edge.

        Identifier (id) of a QueryGraph QEdge in this same message that yielded this Edge in the KnowledgeGraph  # noqa: E501

        :return: The qedge_id of this Edge.
        :rtype: str
        """
        return self._qedge_id

    @qedge_id.setter
    def qedge_id(self, qedge_id: str):
        """Sets the qedge_id of this Edge.

        Identifier (id) of a QueryGraph QEdge in this same message that yielded this Edge in the KnowledgeGraph  # noqa: E501

        :param qedge_id: The qedge_id of this Edge.
        :type qedge_id: str
        """

        self._qedge_id = qedge_id
