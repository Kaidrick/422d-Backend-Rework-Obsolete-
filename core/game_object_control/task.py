from core.request.miz.dcs_object import Task, Point
from game_object_control.dcs_set_task import DcsSetTask
from core.request.miz.dcs_env import filter_none_value
import game_object_control.AI as AI


class TaskType:
    MISSION = "Mission"
    ORBIT = "Orbit"
    ATTACK_GROUP = "AttackGroup"
    ATTACK_UNIT = "AttackUnit"
    BOMBING = "Bombing"


class CloseAirSupport(Task):
    def __init__(self):
        super().__init__()
        self.id = "EngageTargets"
        self.key = "CAS"
        self.enabled = True
        self.auto = True
        self.params = {
            'targetTypes': [
                "Helicopters", "Ground Units", "Light armed ships",
            ],
            'priority': 0,
        }


class AttackGroup(DcsSetTask):
    def __init__(self, group_id, delay=0, weapon_type=None, expend=None,
                 direction_enabled=None, direction=None, altitude_enabled=None,
                 altitude=None, attack_qty_limit=None, attack_qty=None):
        super().__init__(TaskType.ATTACK_GROUP, group_id, delay)
        self.id = 'AttackGroup'
        self.params = {
            'groupId': group_id,
            'weaponType': weapon_type,
            'expend': expend,
            'directionEnabled': direction_enabled,
            'direction': direction,
            'altitudeEnabled': altitude_enabled,
            'altitude': altitude,
            'attackQtyLimit': attack_qty_limit,
            'attackQty': attack_qty,
        }


class AttackUnit(DcsSetTask):
    def __init__(self, group_id, unit_id, delay=0, weapon_type=None, expend=None,
                 direction=None, attack_qty_limit=None, attack_qty=None,
                 group_attack=None):
        super().__init__(TaskType.ATTACK_UNIT, group_id, delay)
        self.id = 'AttackGroup'
        self.params = {
            'unitId': unit_id,
            'weaponType': weapon_type,
            'expend': expend,
            'direction': direction,
            'attackQtyLimit': attack_qty_limit,
            'attackQty': attack_qty,
            'groupAttack': group_attack,
        }


class Bombing(DcsSetTask):
    def __init__(self, group_id, point, attack_qty, delay=0, weapon_type=None,
                 expend=None, direction=None, group_attack=None,
                 altitude=None, altitude_enabled=None):
        super().__init__(TaskType.BOMBING, group_id, delay)
        self.params = {
            'point': point,
            'weaponType': weapon_type,
            'expend': expend,
            'attackQty': attack_qty,
            'direction': direction,
            'groupAttack': group_attack,
            'altitude': altitude,
            'altitudeEnabled': altitude_enabled,
        }

    def clean(self):
        self.params = filter_none_value(self.params)


class Orbit(DcsSetTask):
    def __init__(self, group_id, pattern, delay=0, point=None, point2=None, speed=None, altitude=None):
        super().__init__(TaskType.ORBIT, group_id, delay)
        self.params = {
            'pattern': pattern,
            'point': point,
            'point2': point2,
            'speed': speed,  # default 1.5 stall speed
            'altitude': altitude,
        }

    def clean(self):
        self.params = filter_none_value(self.params)


class Mission(DcsSetTask):
    def __init__(self, group_id=None, delay=0):
        super().__init__(TaskType.MISSION, group_id, delay)
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


if __name__ == '__main__':
    from core.request.miz.dcs_object import Group, Unit

    # new_enroute_task = game_object_control.enroute_task.Tanker("PETRO")

    # p1 = Point("start", -358273, 4142)
    # p1.type = "Turning Point"
    # p1.action = "Turning Point"
    # p1.alt = 5000
    # p1.alt_type = "BARO"
    # p1.task = {
    #     'id': "ComboTask",
    #     'params': {
    #         'tasks': {
    #
    #         }
    #     }
    # }
    # p1.speed = 140
    #
    #
    # p2 = Point("fin", -335001, 12489)
    # p2.type = "Turning Point"
    # p2.action = "Turning Point"
    # p2.alt = 5000
    # p2.alt_type = "BARO"
    # p2.task = {
    #     'id': "ComboTask",
    #     'params': {
    #         'tasks': {
    #
    #         }
    #     }
    # }
    # p2.speed = 140
    #
    # new_mission = Mission("PETRO")
    # new_mission.add_route_point([p1.__dict__, p2.__dict__])
    # print(new_mission.__dict__)
    #
    # # new_mission.send()
    #
    # # orbit_task = Orbit("PETRO", AI.Task.OrbitPattern.CIRCLE).send()
    # # print(orbit_task.as_task())
    #
    # new_orbit_task = Orbit("PEGASUS #001", AI.Task.OrbitPattern.RACE_TRACK)
    # new_orbit_task.params['point'] = {'x': -358273, 'y': 5000, 'z': 4142}
    # new_orbit_task.params['point2'] = {'x': -397301, 'y': 5000, 'z': -67367}
    # # new_orbit_task.send()
    #
    # # new_enroute_task.send()
    #
    # orbit_task = Orbit("TEST", AI.Task.OrbitPattern.CIRCLE).send()
    #
    # bombing = Bombing("TEST", {'x': -337891, 'y': -55409}, 4)
    # bombing.clean()
    # bombing.send()
    # print(bombing.__dict__)




    tanker_group = Group("TANKER", None, None)
    # tanker_group.modulation = 0
    # tanker_group.tasks = {}
    # tanker_group.radioSet = False
    tanker_group.task = "Refueling"
    # tanker_group.uncontrolled = False

    # tanker_group.hidden = False

    # tanker_group.x = -398865.625
    # tanker_group.y = -17143.28515625
    # tanker_group.start_time = 0
    # tanker_group.frequency = 251
    # tanker_group.communication = True

    tanker_unit = Unit("PETRO", None, None)
    tanker_unit.skill = "Excellent"
    tanker_unit.parking = 206
    tanker_unit.type = "KC130"
    # tanker_unit.parking_id = "G28"
    # tanker_unit.x = -398865.625
    # tanker_unit.y = -17143.28515625
    # tanker_unit.heading = 0.23547549107691
    tanker_unit.onboard_num = "012"
    # tanker_unit.speed = 0
    # tanker_unit.psi = -0.23547549107691
    # tanker_unit.alt = 567
    # tanker_unit.alt_type = "BARO"
    # tanker_unit.livery_id = "default"
    # tanker_unit.unitID = 5
    tanker_unit.payload = {
        'pylons': {},
        'fuel': 20830,  # how to get fuel number
        'flare': 60,
        'chaff': 120,
        'gun': 100
    }

    tanker_group.add_unit(tanker_unit)
    print(tanker_group.__dict__)

    tanker_task = Task()
    tanker_task.id = "Tanker"
    tanker_task.auto = True
    tanker_task.enabled = True
    tanker_task.params = {}

    tanker_beacon = Task()
    tanker_beacon.id = "ActivateBeacon"
    tanker_beacon.auto = True
    tanker_beacon.enabled = True
    tanker_beacon.params = {
        'type': 4,
        'frequency': 1088000000,
        'callsign': 'TKR',
        'channel': 1,
        'modeChannel': 'X',
        'bearing': True,
        'system': 4,
    }

    task_list = [tanker_task.bake()]
    for idx, task in enumerate(task_list):
        task['number'] = idx + 1

    sp = Point(None, None, None)
    sp.action = "From Parking Area"
    sp.speed = 0
    sp.type = AI.Task.WaypointType.TAKEOFF_PARKING
    sp.airdromeId = 4
    sp.add_task(task_list)

    p1 = Point(None, None, None)
    p1.alt = 2000
    p1.action = "Turning Point"
    p1.alt_type = "BARO"
    p1.type = "Turning Point"
    p1.x = -380143.81928462
    p1.y = -12651.427669193
    # p1.add_task([])

    print(sp.task)
    # print(p1.task)

    tanker_group.add_route_points([sp])

    print(tanker_group.bake())

    from game_object_control.dcs_spawn import AddGroup
    AddGroup(tanker_group.__dict__).send()


    # RequestDcsDebugCommand(cmd).send()

    orbit_task = Orbit("TANKER", AI.Task.OrbitPattern.CIRCLE)
    orbit_task.clean()
    print(orbit_task.__dict__)
    orbit_task.send()

