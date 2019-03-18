from core.request.miz.dcs_action import ActionType, DcsAction


class AddStaticObject(DcsAction):
    def __init__(self, name, object_type, x, y, country="usa", livery_id="", onboard_num=0, heading=0):
        super().__init__(action_type=ActionType.ADD_STATIC)
        self.object = {
            'name': name,
            'type': object_type,
            'x': x,
            'y': y,
            'livery_id': livery_id,
            'onboard_num': onboard_num,
            'heading': heading,
            'country': country,
        }


class AddGroup(DcsAction):
    def __init__(self, group_data, country=2, category=0):
        super().__init__(action_type=ActionType.ADD_GROUP)
        self.group_data = group_data
        self.country = country
        self.category = category
