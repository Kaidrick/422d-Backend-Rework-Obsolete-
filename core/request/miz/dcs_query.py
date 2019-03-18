from core.request.miz.dcs_request import RequestDcs, RequestHandle


class QueryCategory:
    COALITION_ALL_GROUP = "groups_data_by_coal"
    ENV_ALL_GROUP = "groups_data_all_coal"
    COALITION_ALL_STATIC_OBJECT = "static_objects_by_coalition"
    ENV_ALL_STATIC_OBJECT = "static_objects_all_coal"
    MARK_PANEL = "user_mark"


class RequestDcsInfo(RequestDcs):
    def __init__(self):
        super().__init__(RequestHandle.QUERY)


class RequestDcsGroupsByCoalition(RequestDcsInfo):
    def __init__(self, side):
        super().__init__()
        self.coalition = side
        self.type = QueryCategory.COALITION_ALL_GROUP


class RequestDcsAllGroups(RequestDcsInfo):
    def __init__(self):
        super().__init__()
        self.type = QueryCategory.ENV_ALL_GROUP


class RequestDcsStaticObjectsByCoalition(RequestDcsInfo):
    def __init__(self, side):
        super().__init__()
        self.coalition = side
        self.type = QueryCategory.COALITION_ALL_STATIC_OBJECT


class RequestDcsAllStaticObjects(RequestDcsInfo):
    def __init__(self):
        super().__init__()
        self.type = QueryCategory.ENV_ALL_STATIC_OBJECT


class RequestMarkPanel(RequestDcsInfo):
    def __init__(self):
        super().__init__()
        self.type = QueryCategory.MARK_PANEL


if __name__ == '__main__':
    print(RequestDcsAllStaticObjects().send())
    # from core.request.miz.dcs_debug import RequestDcsDebugCommand
    #
    # mark_panels = RequestMarkPanel().send()
    # print(mark_panels)
    # for mark_panel in mark_panels:
    #     print("Idx", mark_panel['idx'], "groupID", mark_panel['groupID'])
    # # need to find the max id
    # # cmd = """trigger.action.markToAll(251658255, "Nellis AFB Point", {x = -398169, z = -17295, y = 1486.7826147108}, true, "GO!")"""
    # # RequestDcsDebugCommand(cmd, True, True).send()
    #
    # cmd_mark_to_group = """
    #     trigger.action.markToGroup(1, "Read only mark to group 722", {x = -393569, z = -17395, y = 1486.7826147108}, 722 , true, "A read only mark is added.")
    # """
    # RequestDcsDebugCommand(cmd_mark_to_group).send()
