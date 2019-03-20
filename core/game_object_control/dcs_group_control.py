from core.request.miz.dcs_object import Group, Unit, Point
import core.game_object_control.AI as AI
from core.game_object_control.task import Mission


# TODO: generate airport information for nav use
# TODO:


# DCS: generate points for route
class Flight:  # Control the init of an aircraft or helicopter group
    """
    The absolute must have parameters for the group data is:
    group_name
    task
    units:
        unit_name,
        unit_type,
        x, y or start location such as helipad or airport position

    this class only initiate the group, so it only needs the information
    for a start point in route
    """
    def __init__(self, name, task, x=None, y=None, group_id=None):
        self.group_data = Group(name, x, y)
        self.group_data.task = task
        self.group_data.groupId = group_id
        self.group_data.communication = True

        self.init_data = {}

    def section(self, num_ac, ac_type, ls_pos=None, ls_skill=None, ls_ob_num=None,
                ls_livery_id=None, ls_parking=None, speed=None, payload=None,
                ls_unit_id=None, ls_callsign=None):  # each itme in ls_callsign is a list {1, 1, 1, name: stg}

        self.init_data['units'] = {
            'ships': num_ac,
            'type': ac_type,
            'ls_unitId': ls_unit_id,
            'livery_id': ls_livery_id,
            'parking': ls_parking,
            'speed': speed,
            'payload': payload,
            'skills': ls_skill,
            'onboard_num': ls_ob_num,
            'pos': ls_pos,
            'callsign': ls_callsign
        }

        return self

    def init_units(self):
        for idx in range(0, self.init_data['units']['ships']):
            ac_unit = Unit(f"{self.group_data.name} {idx+1}", None, None)
            ac_unit.type = self.init_data['units']['type']
            ac_unit.payload = {  # find payload method?
                'pylons': {},
                'fuel': 99999999999,  # how to get fuel number 20830
                'flare': 60,
                'chaff': 120,
                'gun': 100
            }
            ac_unit.onboard_num = self.init_data['units']['onboard_num']
            if self.init_data['units']['callsign']:
                ac_unit.callsign = [self.init_data['units']['callsign'][idx][0],
                                    self.init_data['units']['callsign'][idx][1],
                                    self.init_data['units']['callsign'][idx][2],
                                    {'name': self.init_data['units']['callsign'][idx][3]}]

            if 'ls_parking' in self.init_data.keys() and self.init_data['ls_parking']:
                ac_unit.parking = self.init_data['ls_parking'][idx]
                print(ac_unit.parking)

            if 'ls_unitId' in self.init_data.keys() and self.init_data['ls_unitId']:
                ac_unit.unitId = ac_unit.parking = self.init_data['ls_unitId'][idx]

            self.group_data.add_unit(ac_unit)

    def base(self, ab_id, ls_parking=None, rdy="cold"):  # start location is a dict?
        self.init_data['ls_parking'] = ls_parking

        sp = Point(None, None, None)

        if rdy == "cold":
            # print(rdy)
            sp.action = "From Parking Area"
            sp.type = "TakeOffParking"
            sp.airdromeId = ab_id

        elif rdy == "hot":
            print(rdy)
        elif rdy == "runway":
            print(rdy)

        # init units
        self.init_units()
        self.group_data.add_route_points([sp])

        return self.group_data.bake()

    def at(self, x, y, alt, alt_type, spd):  # start from air
        sp = Point(None, None, None)
        sp.action = ""
        sp.type = ""
        sp.alt = alt
        sp.alt_type = alt_type
        sp.speed = spd
        sp.x = x
        sp.y = y

        # init units
        self.init_units()
        self.group_data.add_route_points([sp])

        return self.group_data.bake()


def build_point(x, y, action, p_type, alt=None, spd=None, alt_type="BARO", ab_id=None, tasks=None):
    """
    always take imperial data and convert to metric data
    :param x: in-game x
    :param y: in-game y
    :param action:
    :param p_type:
    :param alt: in feet
    :param spd: in knots
    :param alt_type: default to BARO
    :param ab_id:
    :param tasks:
    :return:
    """
    np = Point(None, x, y)
    np.alt = int(float(alt)) / 3.28084  # meters

    np.action = action
    np.alt_type = alt_type
    np.type = p_type
    np.speed = int(float(spd)) / 1.94384  # meters per second
    np.airdromeId = ab_id
    if not tasks:
        np.task = {
            'id': "ComboTask",
            'params': {
                'tasks': {}
            }
        }
    else:
        print("tasks!")
    return np


if __name__ == '__main__':
    from game_object_control.sortie import CAP

    kn_dispatch = Flight("Night Hornets Flight 3", CAP.name, group_id=None)\
        .section(4, "FA-18C_hornet", AI.Skill.EXCELLENT, ls_unit_id=None)\
        .base(4, ls_parking=None, rdy="cold")

    # AddGroup(kn_dispatch).send()

    # Orbit("Night Hornets Flight", AI.Task.OrbitPattern.RACE_TRACK,
    #       point={'x': -358273, 'y': 5000, 'z': 4142},
    #       point2={'x': -208273, 'y': 5000, 'z': -14560}, speed=120, altitude=5000).send()

    cmd = """
    local trash = Group.getByName("Night Hornets Flight")
    trash:destroy()
    """
    # RequestDcsDebugCommand(cmd).send()

    # ep = build_point(-398195.359375, -17233.242188, "Landing", "Land", ab_id=4)

    cnp = build_point(-163811, -236386, "Turning Point", "Turning Point", spd=30)
    nm = Mission("US Battle Group")
    nm.add_route_point([cnp.__dict__])
    nm.send()
