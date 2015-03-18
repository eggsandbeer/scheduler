__author__ = 'Bohdan Mushkevych'

from werkzeug.utils import cached_property

from synergy.conf import settings
from synergy.system import time_helper
from synergy.conf import context
from synergy.mx.rest_models import RestTimetableTreeNode, RestJob
from synergy.mx.mx_decorators import valid_action_request


class TreeNodeDetails(object):
    def __init__(self, mbean, request):
        self.mbean = mbean
        self.process_name = request.args.get('process_name')
        self.timeperiod = request.args.get('timeperiod')
        self.is_request_valid = True if self.mbean else False

    @classmethod
    def get_details(cls, node, as_model=False):
        """method returns either RestJob instance or corresponding document, depending on the as_model argument """
        rest_job = RestJob(
            process_name=node.process_name,
            timeperiod=node.timeperiod,
            time_qualifier=node.time_qualifier,
            number_of_children=len(node.children),
            number_of_failed_calls='NA' if not node.job_record else node.job_record.number_of_failures,
            state='NA' if not node.job_record else node.job_record.state)
        if as_model:
            return rest_job
        else:
            return rest_job.document

    @cached_property
    @valid_action_request
    def details(self):
        rest_node = RestTimetableTreeNode()
        timetable = self.mbean.timetable
        tree = timetable.get_tree(self.process_name)

        if self.timeperiod is None and tree is not None:
            # return list of yearly nodes OR leafs for linear tree
            # limit number of children to return, since a linear tree can holds thousands of nodes
            sorted_keys = sorted(tree.root.children.keys(), reverse=True)
            sorted_keys = sorted_keys[:settings.settings['mx_children_limit']]
            for key in sorted_keys:
                child = tree.root.children[key]
                rest_node.children[key] = TreeNodeDetails.get_details(child)

        elif tree is not None:
            time_qualifier = context.process_context[self.process_name].time_qualifier
            self.timeperiod = time_helper.cast_to_time_qualifier(time_qualifier, self.timeperiod)
            node = tree.get_node(self.process_name, self.timeperiod)
            rest_node.node = TreeNodeDetails.get_details(node, as_model=True)
            for key in node.children:
                child = node.children[key]
                rest_node.children[key] = TreeNodeDetails.get_details(child)

        return rest_node.document
