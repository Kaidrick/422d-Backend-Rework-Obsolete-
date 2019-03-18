class DcsUnit():
    def __init__(self):
        self.player_unit = False
        self.unit_name = ""
        self.unit_id = 666
        self.unit_type = "Ka-50"
        self.unit_pos = {
            'x': 0,
            'y': 0,
            'z': 0,
        }


class DcsPlayer():
    def __init__(self):
        self.player_name = ""
        self.ownership = ""  # current aircraft unit (or maybe ground unit?) in control


class DcsGroup():
    def __init__(self):
        self.player_group = False
        self.name = ""
        self.coalition = ""
        self.id = 666
        self.size = 0
        self.units = []
        self.category = ""
        self.lead_pos = {'x': 0, 'y': 0, 'z': 0}  # the group lead position
        self.radios = []
        self.group_self = {}


class DcsStaticObject:
    def __init__(self):
        self.name = ""
        self.coalition = ""
        self.id = 666
        self.category = 0
        self.pos = {}


# DCS: new object structure
class Category:
    AIRPLANE = 0
    HELICOPTER = 1
    GROUND_UNIT = 2
    SHIP = 3
    STRUCTURE = 4


class Info:
    def bake(self):
        cl_dict = {}
        for key, value in self.__dict__.items():
            if True:
                cl_dict[key] = value
        return cl_dict


class Object(Info):
    def __init__(self, name, x, y, obj_id=0):
        self.name = name
        self.x = x
        self.y = y


class StaticObject(Object):
    def __init__(self, name, x, y):
        super().__init__(name, x, y)


class Group(Object):
    def __init__(self, name, x, y):
        super().__init__(name, x, y)
        self.modulation = None
        self.tasks = None
        self.radioSet = None
        self.task = None
        self.uncontrolled = None
        self.route = None
        self.groupId = None
        self.hidden = None
        self.units = []
        self.communication = None
        self.start_time = None
        self.frequency = None
        self.uncontrollable = None
        self.taskSelected = None

    def add_unit(self, unit_object):
        # add unit dict, check empty value
        unit_dict = {}
        for key, value in unit_object.__dict__.items():
            if value:  # not None value
                unit_dict[key] = value

        self.units.append(unit_dict)

    def add_route_points(self, list_of_points):
        cl_list = []
        for point in list_of_points:
            point_dict = {}
            for key, value in point.__dict__.items():
                if value is not None:
                    point_dict[key] = value
            cl_list.append(point_dict)
        self.route = {
            'points': cl_list
        }

    def bake(self):
        kn_dict = self.__dict__
        clean_dict = {}
        for key, value in kn_dict.items():
            # print(key, value)
            if value is not None:
                clean_dict[key] = value
        return clean_dict


class Unit(Object):
    def __init__(self, name, x, y):
        super().__init__(name, x, y)
        self.alt = None
        self.alt_type = None
        self.livery_id = None
        self.parking = None
        self.parking_id = None
        self.skill = None
        self.speed = None
        self.AddPropAircraft = None
        self.type = None
        self.Radio = None
        self.unitId = None
        self.psi = None
        self.payload = None
        self.heading = None
        self.callsign = None
        self.onboard_num = None
        self.transportable = None
        self.playerCanDrive = None

    # def generate_dict(self):
    #     kn_dict = self.__dict__
    #     clean_dict = {}
    #     for key, value in kn_dict.items():
    #         if value:
    #             print(key, value)
    #             clean_dict[key] = value
    #     return clean_dict


class Point(Object):
    def __init__(self, name, x, y):
        super().__init__(name, x, y)
        self.alt = None
        self.action = None
        self.alt_type = None
        self.speed = None
        self.task = None
        self.type = None
        self.ETA = None
        self.ETA_locked = None
        self.formation_template = None
        self.speed_locked = None
        self.airdromeId = None

    def add_task(self, list_tasks):
        cl_list = []
        for task in list_tasks:
            cl_task = {}
            for key, value in task.items():
                if value is not None:
                    cl_task[key] = value
            cl_list.append(cl_task)

        self.task = {
            'id': "ComboTask",
            'params': {
                'tasks': cl_list
            }
        }


class Task(Info):
    def __init__(self):
        super().__init__()
        self.id = None
        self.enabled = None
        self.key = None
        self.number = None
        self.auto = None
        self.params = None  # params --> tasks --> [1] = {}, [2] = {}


class WrappedActiton:
    def __init__(self):
        self.id = None
        self.params = None


class Payload:
    def __init__(self):
        self.pylons = None
        self.fuel = None
        self.flare = None
        self.ammo_type = None
        self.chaff = None
        self.gun = None  # 0 to 100 percent?


class Callsign:
    def __init__(self, name, first, second, third):
        self.name = name
        self.first = first
        self.second = second
        self.third = third


class Route:
    def __init__(self, list_points=None):
        self.points = list_points

    def add_points(self, list_of_points):  # so this is a list of points
        clean_list = []
        for point in list_of_points:
            kn_dict = point.__dict__
            clean_dict = {}
            for key, value in kn_dict.items():
                if value:
                    clean_dict[key] = value

            clean_list.append(clean_dict)

        self.points = clean_list


def generate_dict(dcs_object):
    kn_dict = dcs_object.__dict__
    clean_dict = {}
    for key, value in kn_dict.items():
        if value:
            clean_dict[key] = value
    return clean_dict
