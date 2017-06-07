"""
Action to add incident type.

A typical use case is to have a Boolean field such as "CSIRT Incident",
available on the New Incident wizard or on the Details form,
to mark the incident as being raised to a CSIRT team from the normal
incident or alert that is handled in triage.

When this field is set: the action sets an Incident Type of "CSIRT"
automatically,  Then Resilient adds the appropriate set of tasks
into the incident.

To configure this action:
- Make an automatic action, named "csirtaction" with the requisite conditions.
  For example, when "CSIRT Confirmed?" equals "Yes".
  This action script doesn't test any conditions itself!
- Use message destination "csirt_action".

"""

from __future__ import print_function
import logging
from circuits.core.handlers import handler
from resilient_circuits.actions_component import ResilientComponent


logger = logging.getLogger(__name__)

CONFIG_DATA_SECTION = "csirt_action"


class IncidentTypeAction(ResilientComponent):
    """Add incident types from custom action"""

    def __init__(self, opts):
        super(IncidentTypeAction, self).__init__(opts)
        self.options = opts.get(CONFIG_DATA_SECTION, {})
        # This action listens to the message destination named "csirt_action"
        self.channel = "actions." + self.options.get("queue", "csirt_action")

    @handler("csirtaction")
    def csirt_action(self, event, *args, **kwargs):
        """Handler for action named 'csirt' (ignoring case)"""
        msg = self._add_incident_type(event, self.options.get("incidenttype", "CSIRT"))
        logger.info(msg)
        yield msg

# Extend this script by adding new handlers for the specific types you want.
# For any Automatic Action, the handler with the same name (lowercase) is run.
#    @handler("apt")
#    def _apt_action(self, event, *args, **kwargs):
#        return self._add_incident_type(event, "APT")

    def _add_incident_type(self, event, incident_type_name):
        """Add incident type to the set of types in the incident"""
        # Here we could verify the incident_type_name,
        # by fetching all the valid values with the Types service.
        # But Resilient will reject the update if the type is not valid,
        # so it's OK (and easier!) to simply let the action fail on error.

        # The get_put() calls this function with the incident to update
        def update_function(incident):
            """Callback function to add `incident_type_name` to the incident types"""
            existing_types = set(incident["incident_type_ids"])
            existing_types.add(incident_type_name)
            new_types = list(existing_types)
            logger.debug("Incident types: " + repr(new_types))
            incident['incident_type_ids'] = new_types
            return incident

        # We want the incident type names as a list of strings,
        # not as a list of IDs, so specify "handle_format=names" in the URL.
        inc_id = event.message["incident"]["id"]
        update_url = "/incidents/{}?handle_format=names".format(inc_id)

        # Update the incident
        newincident = self.rest_client().get_put(update_url, update_function)

        # Return a useful message (visible using the "Action Status" menuitem)
        return "Incident types set to: " + repr(newincident["incident_type_ids"])
