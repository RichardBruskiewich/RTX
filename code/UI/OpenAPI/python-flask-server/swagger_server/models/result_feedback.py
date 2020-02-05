# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from swagger_server.models.base_model_ import Model
from swagger_server.models.feedback import Feedback  # noqa: F401,E501
from swagger_server import util


class ResultFeedback(Model):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    def __init__(self, feedback_list: List[Feedback]=None):  # noqa: E501
        """ResultFeedback - a model defined in Swagger

        :param feedback_list: The feedback_list of this ResultFeedback.  # noqa: E501
        :type feedback_list: List[Feedback]
        """
        self.swagger_types = {
            'feedback_list': List[Feedback]
        }

        self.attribute_map = {
            'feedback_list': 'feedback_list'
        }

        self._feedback_list = feedback_list

    @classmethod
    def from_dict(cls, dikt) -> 'ResultFeedback':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ResultFeedback of this ResultFeedback.  # noqa: E501
        :rtype: ResultFeedback
        """
        return util.deserialize_model(dikt, cls)

    @property
    def feedback_list(self) -> List[Feedback]:
        """Gets the feedback_list of this ResultFeedback.

        List of feedback posts for this result  # noqa: E501

        :return: The feedback_list of this ResultFeedback.
        :rtype: List[Feedback]
        """
        return self._feedback_list

    @feedback_list.setter
    def feedback_list(self, feedback_list: List[Feedback]):
        """Sets the feedback_list of this ResultFeedback.

        List of feedback posts for this result  # noqa: E501

        :param feedback_list: The feedback_list of this ResultFeedback.
        :type feedback_list: List[Feedback]
        """

        self._feedback_list = feedback_list
