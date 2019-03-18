from core.request.miz.dcs_action import DcsAction, ActionType
from core.request.miz.dcs_query import RequestDcsInfo, QueryCategory


MARK_PANEL_IDX_0 = 251658240
total_mission_data = 0


def record_mission_data():
    global total_mission_data
    total_mission_data += 1

    return total_mission_data


class RequestMarkPanels(RequestDcsInfo):
    def __init__(self):
        super().__init__()
        self.type = QueryCategory.MARK_PANEL


class RequestAddMarkPanel(DcsAction):  # add mark panel for group, coalition or all
    def __init__(self, mark_panels):
        super().__init__(ActionType.ADD_MARK_PANEL)
        self.marks = []
        if type(mark_panels) is MarkPanel:  # a single object of MarkPanel
            mark_dict = {
                    'idx': mark_panels.idx,
                    'text': mark_panels.text,
                    'pos': mark_panels.get_pos(),
                    'group_id': mark_panels.group_id,
                    'msg': mark_panels.notice_msg,
                    'read_only': not mark_panels.can_edit  # default read only
            }
            self.marks.append(mark_dict)
            print(self.marks)

        elif type(mark_panels) is list:  # a list of object
            for nmp in mark_panels:
                mark_dict = {
                    'idx': nmp.idx,
                    'text': nmp.text,
                    'pos': nmp.get_pos(),
                    'group_id': nmp.group_id,
                    'msg': nmp.notice_msg,
                    'read_only': not nmp.can_edit  # default read only
                }
                self.marks.append(mark_dict)


class RequestRemoveMarkPanel(DcsAction):  # remove mark panel or a list of mark panel?
    def __init__(self, mark_panels):
        super().__init__(ActionType.RM_MARK_PANEL)
        self.idx = []
        if type(mark_panels) is object:
            self.idx.append(mark_panels.idx)

        elif type(mark_panels) is list:
            for mp in mark_panels:
                self.idx.append(mp.idx)


class MarkPanel:
    def __init__(self, group_id, text, can_edit=False, notice_msg=None):
        self.idx = record_mission_data()
        self.text = text
        self._vec3 = None
        self.can_edit = can_edit
        self.notice_msg = notice_msg
        self.group_id = group_id

    def set_pos(self, x, z, alt=0.0):
        self._vec3 = {'x': x, 'y': alt, 'z': z}
        return self

    def get_pos(self):
        return self._vec3


# TODO: if a player add new user mark in f10 map,
# TODO: then need to use add mark initiator to get player unit, rather than groupID given

def update_mark_panel(mark_panel, text="", pos=None):  # TODO: should accept MarkPanel object or list
    # that is, delete the old panel, and then add a new panel. What to update? pos and text
    RequestRemoveMarkPanel(mark_panel).send()
    updated_mark_panel = mark_panel
    updated_mark_panel.text = text
    if pos:
        updated_mark_panel.set_pos(pos)

    RequestAddMarkPanel(updated_mark_panel).send()
    return updated_mark_panel

# always find the largest idx of existed mark panel before adding anymore new panel
# def get_last_panel_idx():
#     mark_panels = RequestMarkPanels().send()
#     # total_mark_panels = len(mark_panels)  # number of existing mark panels
#     # last_panel_idx = MARK_PANEL_IDX_0 + total_mark_panels
#     try:
#         return mark_panels[-1]['idx']
#     except IndexError:  # maybe there is no mark yet
#         return MARK_PANEL_IDX_0


if __name__ == '__main__':
    # print(RequestDcsAllStaticObjects().send())
    from core.request.miz.dcs_debug import RequestDcsDebugCommand

    i_x = -393569
    i_y = 1486.7826147108
    i_z = -17395
    desc = """
    When the hook is called, its first parameter is a string describing the event that has triggered its call: "call", "return" (or "tail return", when simulating a return from a tail call), "line", and "count". For line events, the hook also gets the new line number as its second parameter. Inside a hook, you can call getinfo with level 2 to get more information about the running function (level 0 is the getinfo function, and level 1 is the hook function), unless the event is "tail return". In this case, Lua is only simulating the return, and a call to getinfo will return invalid data.
    When the hook is called, its first parameter is a string describing the event that has triggered its call: "call", "return" (or "tail return", when simulating a return from a tail call), "line", and "count". For line events, the hook also gets the new line number as its second parameter. Inside a hook, you can call getinfo with level 2 to get more information about the running function (level 0 is the getinfo function, and level 1 is the hook function), unless the event is "tail return". In this case, Lua is only simulating the return, and a call to getinfo will return invalid data.
    When the hook is called, its first parameter is a string describing the event that has triggered its call: "call", "return" (or "tail return", when simulating a return from a tail call), "line", and "count". For line events, the hook also gets the new line number as its second parameter. Inside a hook, you can call getinfo with level 2 to get more information about the running function (level 0 is the getinfo function, and level 1 is the hook function), unless the event is "tail return". In this case, Lua is only simulating the return, and a call to getinfo will return invalid data.
    When the hook is called, its first parameter is a string describing the event that has triggered its call: "call", "return" (or "tail return", when simulating a return from a tail call), "line", and "count". For line events, the hook also gets the new line number as its second parameter. Inside a hook, you can call getinfo with level 2 to get more information about the running function (level 0 is the getinfo function, and level 1 is the hook function), unless the event is "tail return". In this case, Lua is only simulating the return, and a call to getinfo will return invalid data.
    """
    marks = []
    for i in range(1, 3):
        i_x -= 1500
        i_z -= 100
        new_mark = MarkPanel(722, desc, can_edit=False, notice_msg="test panel added.")
        new_mark.set_pos(i_x, i_z, i_y)

        marks.append(new_mark)

    RequestAddMarkPanel(marks).send()

    mp = RequestMarkPanels().send()
    print(mp)
    for mark_panel in mp:
        print("Idx", mark_panel['idx'], "groupID", mark_panel['groupID'])

    # i_x = -393569
    # i_y = 1486.7826147108
    # i_z = -17395
    #
    # new_mark = MarkPanel(722, f"Panel Test {1}", True, notice_msg="test panel added.")
    # new_mark.set_pos(i_x, i_z, i_y)
    #
    # paste = RequestAddMarkPanel(new_mark)
    # print(paste.__dict__)
