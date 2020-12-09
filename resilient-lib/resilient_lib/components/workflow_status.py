# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2020. All Rights Reserved.
# pragma pylint: disable=unused-argument, no-self-use


class WorkflowStatus(object):
    """Class to handle the status of a Workflow Instance"""
    def __init__(self, instance_id, status, start_date, end_date=None, reason=None):
        self.instance_id = instance_id
        self.status = status
        self.start_date = start_date
        self.end_date = end_date
        self.reason = reason
        self.is_terminated = True if status == "terminated" else False

    def __str__(self):
        return "WorkflowStatus {0}: {1}".format(self.instance_id, self.as_dict())

    def as_dict(self):
        """Returns this class object as a dictionary"""
        return self.__dict__

def get_workflow_status(res_client, wf_instance_id):
    """Function to check if the current workflow has been terminated via the UI
    :param res_client: reference to Resilient rest_client()
    :param wf_instance_id: the workflow_instance_id of the current Workflow
    :rtype: WorkflowStatus Object
    """

    if isinstance(wf_instance_id, int) is False:
        raise ValueError("wf_instance_id must be of type int and not {0}".format(type(wf_instance_id)))

    resp = res_client.get("/workflow_instances/{0}".format(wf_instance_id))

    return WorkflowStatus(
        instance_id=wf_instance_id,
        status=resp.get("status"),
        start_date=resp.get("start_date"),
        end_date=resp.get("end_date"),
        reason=resp.get("terminate_reason"))
