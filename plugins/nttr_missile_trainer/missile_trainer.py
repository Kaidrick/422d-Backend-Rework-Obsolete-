"""
This is a file that implements the Missile class
all information of a specific missile is obtained through cdi export
if needed, use miz request to get data? what might be needed though?
"""
import time
import threading
import core.data_interface as cdi
import numpy as np
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from core.request.miz.dcs_event import EventHandler
from core.spark import SparkHandler
from core.request.miz.dcs_debug import RequestDcsDebugCommand
from core.request.miz.dcs_message import RequestDcsMessageForGroup
from core.game_object_control.dcs_set_command import SetInvisible
from core.request.miz.dcs_env import set_msg_locale
import gettext

_ = gettext.gettext


training_missiles = {}

missile_training_range = [
    'ECS', 'EC WEST', 'EC EAST',  # Tonopah Electronic Combat Range(TECR) and Electronic Combat Range South Sector
    '4809B', '4807A',  # consists of a few low altitude SAM site
    'R-75W', 'R-75E',  # Live and Dumb Bombing and gunnery training on high value high threat targets such as AAA, SAMs, Industrial complexes, Radar sites, Trains, Convoys and other high value Military targets such as Bridges
]


def unit_object_by_runtime_id(runtime_id):
    for name, unit_obj in {**cdi.active_players_by_name, **cdi.other_units_by_name}.items():
        if unit_obj.runtime_id == runtime_id:
            return unit_obj

    # after search, none found
    return None


# set player to unprotected state when player enter Electronic Combat Range
# check if player is in range
# set invisible to false
# if player is no longer in range, set invisible to true?

# what about IR missiles?

# how to constrain S-300 AI?
# only if aircraft in specific area will trigger S-300 AI?
# but it will not guarantee attack


class Missile:
    """
    Missile class is a model of a missile. It contains a method to calculate missile speed and distance to
    target.

    When do you create a new object of Missile? On missile launch event, check if ground SAM launch
    """
    def __init__(self, launcher_id, target_id, wpn_object_id, weapon_data):
        self.launcher_id = launcher_id
        self.target_id = target_id  # initial target
        self.wpn_object_id = wpn_object_id

        self.weapon_data = weapon_data

        self.launcher = bake_object_id(self.launcher_id)
        self.target = bake_object_id(self.target_id)
        self.weapon_object = bake_object_id(self.wpn_object_id)

        self.tracking_target = self.get_tracking_target()  # target can change
        self.dist_to_target = None

        self.missile_defeat = []  # a list to track potential defeated, more than five is asserted
        self.last_dist_to_target = None
        self.pos = None

        self.final = False  # final flag, tracker refers to this flag

        try:
            target_unit = unit_object_by_runtime_id(self.target_id)
            target_player_language = target_unit.language
        except KeyError:  # not tracking because target unit no longer exists?
            print("target no longer exists")
            self.fin()
        else:
            self.target_group_id = target_unit.group_id
            self.target_lang = target_player_language

    def target_changed(self):  # if tracking target changes
        # if target has changed, find if target is a player, else ignore
        target = self.tracking_target
        print(target)  # need to know in what form the target is passed
        pass

    def fin(self):
        self.final = True

    def calc_dist_to_target(self):
        retry_count = 0
        while True:

            if self.final:
                print("final, break dist calc")
                break

            if retry_count < 5:
                try:
                    target_unit = unit_object_by_runtime_id(self.target_id)  # only check for player unit
                    target_unit_pos = target_unit.unit_pos

                    missile_unit = cdi.export_units['id_' + str(self.wpn_object_id)]
                    missile_unit_pos = missile_unit.unit_pos
                except KeyError:
                    retry_count += 1
                    time.sleep(1)
                    print("retry calc_dist_to_target")
                    continue
                else:
                    t_pos_array = np.array([target_unit_pos['x'], target_unit_pos['y'], target_unit_pos['z']])
                    m_pos_array = np.array([missile_unit_pos['x'], missile_unit_pos['y'], missile_unit_pos['z']])

                    dist = np.linalg.norm(t_pos_array - m_pos_array)
                    # print(target_unit_pos, missile_unit_pos, str(dist) + " meters")

                    return dist
            else:  # more than 10 retries, break loop, return
                return None

    def check_target_guidance(self):  # check if target still exists? if lock break?
        """
        target is updated every 5 seconds
        distance data is updated every 1 second

        criteria:
            if approx rate is negative for 5 consecutive data, then missile energy drained
            if target is lost, then missile lock broken
            if target

        :return:
        """
        # return if still tracking

        dist = self.calc_dist_to_target()  # try to calculate distance between target and missile
        if not dist:  # fail to find distance, either missile dead or target not exist anymore
            # but it does not mean radar lock break, initial target is dead
            pass

        if self.tracking_target and dist:  # target is updated every 5 seconds while dist is instant

            if self.last_dist_to_target:  # check previous dist
                # if dist is less than previous, missile is approaching
                if dist < self.last_dist_to_target:
                    # print("missile approaching")
                    self.missile_defeat.append(False)
                # else dist is more than previous, missile is defeated
                else:
                    print("missile stops approaching!")
                    self.missile_defeat.append(True)

                # if 10 consecutive defeat than assert defeat
                if len(self.missile_defeat) > 5:
                    defeat = True
                    for d_c in self.missile_defeat:
                        defeat = defeat and d_c  # compare

                    if defeat:
                        print("missile defeated, break tracker")
                        # self.destroy()
                        _ = set_msg_locale(self.target_lang, "missile_trainer")
                        msg = _("Electronic Combat Simulation") + "\n" + \
                            "————————————————————————" + "\n" + \
                            _("Missile Type: ") + \
                            self.weapon_data['weapon_data']['desc']['typeName'] + "\n" + \
                            _("Simulation Result: ") + _("Missile Defeated ") + _("(by Out Maneuvering Missile)")

                        RequestDcsMessageForGroup(self.target_group_id, msg).send()
                        self.final = True
                        return False
                    else:
                        self.missile_defeat.pop(0)

            # save dist
            self.last_dist_to_target = dist
            self.safe_destroy_missile_on_dist(dist)
            return

        # None dist or None target
        else:  # res is None because not tracking or missile no longer exists
            res = self.get_tracking_target()  # check if target break
            if not res:  # confirm target is None
                _ = set_msg_locale(self.target_lang, "missile_trainer")
                msg = _("Electronic Combat Simulation") + "\n" + \
                    "————————————————————————" + "\n" + \
                    _("Missile Type: ") + \
                    self.weapon_data['weapon_data']['desc']['typeName'] + "\n" + \
                    _("Simulation Result: ") + _("Missile Defeated ") + _("(by Breaking Radar Lock)")

                RequestDcsMessageForGroup(self.target_group_id, msg).send()
                self.final = True
                return False
            else:  # target exists but dist cannot be calculate, missile --> dead
                return False

    def safe_destroy_missile_on_dist(self, dist):
        if dist is not None:
            if dist > 1500:
                # print("dist: ", dist)
                return True
            else:  # within hit range, assert hit
                self.destroy()
                _ = set_msg_locale(self.target_lang, "missile_trainer")
                msg = _("Electronic Combat Simulation") + "\n" + \
                      "————————————————————————" + "\n" + \
                      _("Missile Type: ") + \
                      self.weapon_data['weapon_data']['desc']['typeName'] + "\n" + \
                      _("Simulation Result: ") + _("Missile Hit")

                RequestDcsMessageForGroup(self.target_group_id, msg).send()

                print("missile self destroy, break tracker")
                self.final = True
                return False

        else:  # return None dist because cdi data error
            print("cannot find data in cdi, abort")
            self.final = True
            self.destroy()
            return False

    def get_tracking_target(self):
        cmd = f""" -- still need to use protected call here, or dcs will freeze
        success, res = pcall(
            function()
                return Weapon.getTarget({bake_object_id(self.wpn_object_id)})
            end
        )
        if success then
            return res
        else
            return nil
        end
        """
        res = RequestDcsDebugCommand(cmd, True).send()  # {'id_': 16880129}
        # print(res)
        if self.tracking_target is not res:  # different target? on initial or target change
            self.target_changed()
        else:  # still the same target
            pass

        self.tracking_target = res
        print(res)
        return res

    def destroy(self):  # destroy this missile
        cmd = f"""
        success, res = pcall(
            function()
                Weapon.destroy({bake_object_id(self.wpn_object_id)})
            end
        )
        return success
        """
        destroyed = RequestDcsDebugCommand(cmd, True).send()
        if destroyed:
            print("missile destroyed")
        else:
            print(__file__, "some error occurred while trying to destroy missile.")

    def target_tracker(self):
        while True:
            res = self.get_tracking_target()
            if not res:
                print("get tracking target fail, break")
                break

            time.sleep(5)

    def start_tracking(self):
        print('missile.py', f'start tracking weapon {self.weapon_object}')
        self.get_tracking_target()  # always get target once
        threading.Thread(target=self.target_tracker).start()  # start target tracker thread
        while True:
            # still_tracking = self.check_target_guidance()

            if self.tracking_target:  # still guided to a target
                # check missile distance and if defeated
                self.check_target_guidance()
            else:  # does not have a target
                self.final = True
                print("tracker ends")
            #
            # if not still_tracking:  # not tracking
            #     self.final = True
            #     print("tracker ends")
                #
                # try:
                #     target_unit = cdi.active_players_by_unit_runtime_id['id_' + str(self.target_id)]
                # except KeyError:  # not tracking because target unit no longer exists?
                #     print("target no longer exists")
                # else:
                #     target_group_id = target_unit.group_id
                #     RequestDcsMessageForGroup(target_group_id, "Missile Defeated!").send()

                break

            time.sleep(1)


def bake_object_id(obj_id):
    return f"""{{['id_'] = {obj_id},}}"""


def check_sam_launch(event_data):  # add to on shot event, check if missile is from a SAM unit
    """
    :param event_data: find initiator and find weapon data
    must not be player controlled
    category should be 1 --> missile?
    missileCategory --> what is this though?
    {
        'initiator_runtime_id'
        'initiator_type'
        'player_control'
        'weapon_data': {
            'name'
            'object'
            'launcher_group_id'
            'launcher_object'
            'launcher_vector_data'  # p, x, y, z
            'category'
            'desc': {
                'category'
                'displayName'
                'missileCategory'
                'typeName'
            }
            'vector_data'
        }

    }
    'typeName'
    :return:
    """
    # AI controlled SAM only
    if not event_data['player_control'] and event_data['weapon_data']['desc']['missileCategory'] == 2:
        # TODO: weapon must be missile!
        # TODO: launcher must be ground unit!
        launcher_runtime_id = event_data['initiator_runtime_id']  # without 'id_' prefix
        launcher_type = event_data['initiator_type']
        wpn_type_name = event_data['weapon_data']['desc']['typeName']
        wpn_object_id = event_data['weapon_data']['object']['id_']

        # try:
        #     target = event_data['target_data']
        # except KeyError:
        #     print(__file__, "def check_sam_launch", "no target data")
        # else:
        #     print(target)

        try:
            cmd = f""" -- still need to use protected call here, or dcs will freeze
            success, res = pcall(
                function()
                    return Weapon.getTarget({bake_object_id(wpn_object_id)})
                end
            )
            if success then
                return res
            else
                return nil
            end
            """
            res = RequestDcsDebugCommand(cmd, True).send()  # {'id_': 16880129}
        except Exception as e:
            print(e)
        else:  # is a value is returned (whatever, may even be None or [] or {})
            # check if target is in cdi
            target_export_id = res['id_']

            # create new missile object
            new_missile = Missile(launcher_runtime_id, target_export_id, wpn_object_id, event_data)
            training_missiles[wpn_object_id] = new_missile

            threading.Thread(target=new_missile.start_tracking).start()

            # send trigger message to target?

            target_player = unit_object_by_runtime_id(target_export_id)
            target_pos = target_player.unit_pos
            target_group_id = target_player.group_id
            target_lang = target_player.language

            missile_launch_pos = event_data['weapon_data']['vector_data']['p']

            target_pos_array = np.array([target_pos['x'], target_pos['y'], target_pos['z']])
            missile_launch_pos_array = np.array([missile_launch_pos['x'],
                                                 missile_launch_pos['y'],
                                                 missile_launch_pos['z']])

            # from target to missile
            vector_to_missile = missile_launch_pos_array - target_pos_array

            print(target_pos_array, missile_launch_pos_array, vector_to_missile)

            dist = np.linalg.norm(vector_to_missile)  # distance in meters

            # need to find direction
            print(vector_to_missile[2], vector_to_missile[0], vector_to_missile[2] / vector_to_missile[0])
            raw_hdg = np.arctan(vector_to_missile[2] / vector_to_missile[0])
            print(raw_hdg)

            if vector_to_missile[2] < 0:  # z is less than zero
                hdg = raw_hdg + np.pi
            else:
                hdg = raw_hdg

            # get north correction
            nc_x = target_pos['x']
            nc_y = target_pos['y']
            nc_z = target_pos['z']
            cmd = f"""return getNorthCorrection({{x = {nc_x}, y = {nc_y}, z = {nc_z}}})"""
            nc = RequestDcsDebugCommand(cmd, True).send()

            p_hdg = np.rad2deg(nc + hdg)

            if p_hdg < 0:
                p_hdg += 360

            _ = set_msg_locale(target_lang, "missile_trainer")
            msg = _("Electronic Combat Simulation") + "\n" + \
                "————————————————————————" + "\n" + \
                _("Missile Launch: ") + event_data['weapon_data']['desc']['typeName'] + "\n" + \
                _("HDG ") + f"{p_hdg:03.0f}" + _(" for ") + \
                f"{dist / 1852:.0f}" + _(" nm")  # need to add launcher type as well

            RequestDcsMessageForGroup(target_group_id, msg).send()

        print(launcher_runtime_id, launcher_type, wpn_type_name)

    pass


def protect(player_name):  # set all aircraft to invisible when spawn FIXME: all aircraft, player only now
    # test set invisible, should only attack once
    target_unit = cdi.active_players_by_name[player_name]
    player_group_name = target_unit.player_group_name
    SetInvisible(player_group_name).send()
    print(f"set {player_name} invisible")
    target_unit.invisible_to_ai = True


def unprotect(player_name):
    # test set invisible, should only attack once
    target_unit = cdi.active_players_by_name[player_name]
    player_group_name = target_unit.player_group_name
    SetInvisible(player_group_name, False).send()
    print(f"undo {player_name} invisible")
    target_unit.invisible_to_ai = False


def protect_new_player_spawn(spk_dt):
    player_name = spk_dt['data']['name']
    protect(player_name)
    pass


def player_tracker():  # track all player position (if in range)
    while True:
        for player_name, player_dt in cdi.active_players_by_name.items():
            p_as = player_dt.get_airspace()
            if p_as and p_as in missile_training_range:
                # if player is in a defined airspace
                # is player already registered to this airspace?
                if player_dt.invisible_to_ai:  # player is invisible to AI, unprotect
                    unprotect(player_name)
                    player_dt.invisible_to_ai = False
                else:  # player is already unprotected, do nothing
                    pass

            else:  # not in range, do nothing. but if player enters range then leave, need to re-protect
                if not player_dt.invisible_to_ai:
                    protect(player_name)
                else:  # player is already protected
                    pass

        time.sleep(5)

    # use an airspace change event?


def declare():
    threading.Thread(target=player_tracker).start()
    EventHandler.SHOT['nttr_missile_trainer_check_sam_launch'] = check_sam_launch
    SparkHandler.PLAYER_SPAWN['nttr_missile_trainer_protect_new_player_spawn'] = protect_new_player_spawn


