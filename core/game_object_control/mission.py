# always use mission to issue task
# always use command to execute command
# always use option to set option
from game_object_control.dcs_set_task import DcsSetTask


def filter_none_value(kn_dict):
    clean_dict = {}
    for key, value in kn_dict.items():
        if value:  # not None value
            clean_dict[key] = value

    return clean_dict


# DCS Object Control: Mission
class Mission(DcsSetTask):
    def __init__(self, group_id, delay=0):
        super(Mission, self).__init__(None, group_id, delay)
        self.id = 'Mission'
        self.params = {
            'route': {
                'points': [

                ],
            },
        }

    def add_route_point(self, list_points):
        for point in list_points:
            self.params['route']['points'].append(filter_none_value(point.__dict__))


class Tanker:
    def __init__(self, tcn_callsign, tcn_channel, tcn_mode, alt, spd, p1=None, p2=None):
        self.tasks = [
            {
                'number': 1,
                'auto': False,
                'id': "Tanker",
                'enabled': True,
                'params': {},
            },

            {
                'number': 2,
                'auto': False,
                'id': "Orbit",
                'enabled': True,
                'params': {
                    'pattern': "Race-Track",
                    'point': p1,
                    'point2': p2,
                    'speed': spd / 1.94384,  # default 1.5 stall speed
                    'altitude': alt / 3.28084,
                },
            },
        ]


# WrappedAction
class WrappedAction:
    def __init__(self, action_id, params):
        self.id = "WrappedAction"
        self.enable = True
        self.auto = True
        self.number = None
        self.params = {
            'action': {
                'id': action_id,
                'params': params,
            }
        }


if __name__ == '__main__':
    tkr = Tanker("TKR", 7, "X", 5000, 150)
    print(tkr.tasks)

