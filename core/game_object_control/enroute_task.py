from game_object_control.dcs_set_task import DcsSetTask


class EnRouteTaskType:
    TANKER = "Tanker"
    AWACS = "AWACS"


class Tanker(DcsSetTask):
    def __init__(self, group_id, delay=0):
        super().__init__(EnRouteTaskType.TANKER, group_id, delay)
        self.params = {}


class AWACS(DcsSetTask):
    def __init__(self, group_id, delay=0):
        super(AWACS, self).__init__(EnRouteTaskType.AWACS, group_id, delay)
        self.params = {}
