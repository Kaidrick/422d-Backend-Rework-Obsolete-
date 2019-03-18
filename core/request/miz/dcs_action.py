from core.request.miz.dcs_request import RequestHandle, RequestDcs


class ActionType:
    DESTROY_OBJECT = 0
    ADD_GROUP = 1
    ADD_STATIC = 2
    ADD_STATIC_GROUP = 3
    ADD_RADIO = 4
    RM_RADIO = 5
    SANITIZE_RADIO = 6
    CONTROLLER = 7
    ADD_MARK_PANEL = 8  # including add for all, coalition and group, use params to control
    RM_MARK_PANEL = 9


class DcsAction(RequestDcs):  # an action request, that is, request to do some action
    def __init__(self, action_type):
        super().__init__(handle=RequestHandle.ACTION)
        self.type = action_type
