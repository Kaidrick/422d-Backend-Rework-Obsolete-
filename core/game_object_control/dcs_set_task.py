from core.request.miz.dcs_action import DcsAction, ActionType


class DcsSetTask(DcsAction):  # command is always set to a group or a unit?
    def __init__(self, cmd_id, group_id, delay=0):  # group id?
        # so lua should know these attributes
        super().__init__(ActionType.CONTROLLER)
        self.control_action = "set_task"
        self.id = cmd_id
        self.group_id = group_id
        self.delay = delay
