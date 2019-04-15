import core.data_interface as cdi
import core.utility.utils as utils
import core.utility.data_parsing as parse
import time
from .target_data import get_target_position_lua_object
from .missile_training_announcer import report_simulation_result, MissileControlRelease
from core.request.miz.dcs_debug import RequestDcsDebugCommand
import numpy as np
from collections import deque


def unit_object_by_runtime_id(runtime_id):
    for name, unit_obj in {**cdi.active_players_by_name, **cdi.other_units_by_name}.items():
        if unit_obj.runtime_id == runtime_id:
            return unit_obj

    # after search, none found
    return None


class Missile:
    """
    Basic Missile Class
    This class should be extended by other missile class in order to implement
    control step method and other related fields
    """
    def __init__(self, launcher_id, wpn_object_id, weapon_data):
        # passed parameters
        self.launcher_id = launcher_id  # without id_ prefix
        self.wpn_object_id = wpn_object_id
        self.weapon_data = weapon_data

        # launcher and weapon lua object
        self.launcher = utils.bake_object_id(self.launcher_id)
        self.weapon_object = utils.bake_object_id(self.wpn_object_id)

        # essential missile data
        self.last_speeds = []

        # defeats
        self.missile_defeat_spd = []  # a list to track potential defeated, more than five is asserted
        self.missile_defeat_app = []

        # get launcher's position
        launcher_pos = unit_object_by_runtime_id(self.launcher_id).unit_pos
        self.current_pos = launcher_pos  # same position as launcher

        # TODO: maybe need to make a set of method to track launcher pos/movement/dist as well
        self.launcher_pos = launcher_pos  # what if launcher is moving?

        # set initial target for all missile, either a target dict or None
        self.initial_target = self.update_tracking_target()  # returns a target object or None
        print(f"{self.wpn_object_id}, initial target is {self.initial_target}")

        self.old_target = None
        self.current_target = self.initial_target  # FIXME: always show DECOY message

        # for log data purpose
        self.control_release_reason = None

        # miscellaneous
        self.launch_noticed = False

    # every missile should have a target change methods? to update target?
    def target_change(self, new_target):  # new target could be a Player object or None
        self.old_target = self.current_target
        self.current_target = new_target
        print(self.wpn_object_id, "target change", self.old_target, self.current_target)

    def assert_defeat_on_criteria(self, comparison_set: list, criteria_result: bool):
        if len(comparison_set) > 9:
            defeat = criteria_result
            for record_result in comparison_set:
                defeat = defeat and record_result
            # after and test
            # record this criteria result anyway
            comparison_set.pop(0)  # take out the oldest result
            comparison_set.append(criteria_result)
            # print(comparison_set)
            return defeat
        else:  # has less than 4 data, not enough record to assert missile defeat
            comparison_set.append(criteria_result)
            return False

    def update_tracking_target(self):
        # so here is the thing:
        # every missile can update its tracking target
        # but the target is not necessarily a player, it could be something else
        # FIXME: what about other missiles or AI aircraft or so?
        # Temp Solution: Try block
        cmd = f""" -- still need to use protected call here, or dcs will freeze
        success, res = pcall(function() return Weapon.getTarget({utils.bake_object_id(self.wpn_object_id)}) end)
        if success then return res else return nil end"""
        res = RequestDcsDebugCommand(cmd, True).send()  # {'id_': 16880129}
        try:  # try to get this id in active_players_by_unit_runtime_id
            target_obj = unit_object_by_runtime_id(res['id_'])
        except KeyError:  # player does not exist, or target is actually something else
            target_obj = None

        return target_obj  # return a core.functions.map_units.Player object, or None

    def update_missile_position(self):  # and launcher position?
        q_str = 'id_' + str(self.wpn_object_id)
        try:
            msl_pos = cdi.active_munition[q_str].trajectory[-1]
        except KeyError:  # missile does not exist in mission
            return None
        else:
            self.current_pos = msl_pos
            return self.current_pos

    # TODO: not used at the moment
    def update_launcher_position(self):  # is this necessary?
        try:  # so launcher might be a Player or OtherUnits
            lnc_pos = unit_object_by_runtime_id(self.launcher_id).unit_pos
        except KeyError:  # not in an AI unit
            lnc_pos = None

        self.launcher_pos = lnc_pos
        return lnc_pos

    # every missile should have a speed... for sure
    def missile_get_speed(self):  # return speed or None if data is insufficient
        msl = cdi.active_munition['id_' + str(self.wpn_object_id)]
        # msl_recent_pos = msl.recent_pos
        # msl_recent_pos_time = msl.recent_pos_time
        # msl_spd = parse.position_change_over_time_difference(
        #     msl_recent_pos, msl_recent_pos_time
        # )
        msl_spd = msl.terminal_speed[-1]
        # print(self.wpn_object_id, f"spd {msl_spd} m/s")
        return msl_spd  # in meters per second

    # relative position vector
    def get_relative_position_vector(self):
        msl_pos = self.current_pos
        tgt_pos = self.current_target.unit_pos
        pos_vel = utils.pos_to_np_array(tgt_pos) - utils.pos_to_np_array(msl_pos)
        return pos_vel

    # approach vector: relative movement from missile to target, V_m -V_t = V_app
    def get_approach_vector(self):
        # find target velocity vector
        # find missile velocity vector
        # V_m - V_t
        msl = cdi.active_munition['id_' + str(self.wpn_object_id)]
        msl_recent_pos = msl.trajectory
        msl_recent_pos_time = msl.timestamp

        tgt = self.current_target
        # tgt_recent_pos = tgt.recent_pos
        # tgt_recent_pos_time = tgt.recent_pos_time

        msl_vel = parse.calc_velocity(msl_recent_pos, msl_recent_pos_time)
        # tgt_vel = parse.calc_velocity(tgt_recent_pos, tgt_recent_pos_time)
        tgt_vel = np.array([
            tgt.velocity['x'], tgt.velocity['y'], tgt.velocity['z']
        ])

        # np.array V_missile - V_target
        # TypeError: unsupported operand type(s) for -: 'NoneType' and 'float', how?
        # msl_vel is None?
        try:
            app_vel = msl_vel - tgt_vel
        except TypeError:  # likely that msl_vel is None because there is no enough data
            return None
        else:
            return app_vel

    def get_missile_approach(self):
        # check if the angle between approach vector and relative position vector is less than pi/2
        pos_vel = self.get_relative_position_vector()
        msl_app_vel = self.get_approach_vector()
        if msl_app_vel is None:
            return None, None  # not enough data
        app_rate = np.linalg.norm(msl_app_vel)
        r_agl = parse.angle_between(pos_vel, msl_app_vel)
        return r_agl, app_rate

    def check_missile_approach(self):
        missile_approach_angle, missile_approach_rate = self.get_missile_approach()
        if missile_approach_angle:
            # print("approach angle is", np.rad2deg(missile_approach_angle))
            if abs(missile_approach_angle) > 90 or missile_approach_rate < 100:
                return True  # very bad approach, defeat
            else:  # still a potential threat with high energy, keep tracking control
                return False  # good approach with decent approach rate
        else:  # not enough data to calculate missile approach
            return None

    def destroy(self):  # destroy this missile
        cmd = f"""success, res = pcall(function() Weapon.destroy({utils.bake_object_id(self.wpn_object_id)}) end)
        return success"""
        destroyed = RequestDcsDebugCommand(cmd, True).send()
        if destroyed:
            print("missile destroyed")
        else:
            print(__file__, "some error occurred while trying to destroy missile.")

    def safe_destroy_missile_in_range(self, dist, safe_destroy_dist=1500):
        try:
            if dist < safe_destroy_dist:
                self.destroy()
                return True  # is missile destroy
            else:  # out of safe destroy dist
                return False
        except TypeError:
            return None

    def safe_missile_speed(self, safe_msl_spd=250):
        msl_spd = self.missile_get_speed()
        try:
            if msl_spd < safe_msl_spd:
                return True  # missile below maneuvering speed
            else:  # missile still has high energy
                return False
        except TypeError:
            return None


# a missile can re-acquire target, it has old target and new target and no target as well
class MissileCanReacquire(Missile):
    def __init__(self, launcher_id, wpn_object_id, weapon_data):
        super().__init__(launcher_id, wpn_object_id, weapon_data)


# a missile that can only acquire target once, if target is gone then missile is defeated
class MissileCanNotReacquire(Missile):
    def __init__(self, launcher_id, wpn_object_id, weapon_data):
        super().__init__(launcher_id, wpn_object_id, weapon_data)

    def confirm_target_guidance(self):
        if self.current_target:
            try:  # recheck target existence
                target = unit_object_by_runtime_id(self.current_target.runtime_id)
            except KeyError:
                return None
            else:
                return target  # return target object
        else:  # does not have a target
            return None


class SurfaceToAirMissile(MissileCanNotReacquire):
    """
    Surface to Air Missile should only be fired by AI
    and should always have a tracking target
    so a distance to a target can always be calculated
    """
    def __init__(self, launcher_id, wpn_object_id, weapon_data):
        super().__init__(launcher_id, wpn_object_id, weapon_data)

        self.distance_to_target = None

    def control_step(self):  # for SAM only
        # release control
        keep_control = True
        release_reason = None  # an int number

        # update missile position
        pos = self.update_missile_position()
        # print(pos)
        # when step, check if missile still has a target
        target = self.confirm_target_guidance()  # a target object or None
        if target is not self.initial_target:  # target change?
            # assume SAM cannot change back to actual target once decoyed
            keep_control = False
            release_reason = MissileControlRelease.DECOY
        else:  # still has the same target
            if target and pos:  # missile still has a target, missile still exists in missile
                # check if within safe distance, if so destroy missile and report result
                pos_vel = self.get_relative_position_vector()
                dist = np.linalg.norm(pos_vel)  # in meters
                self.distance_to_target = float(dist)
                while True:
                    safe_destroy = self.safe_destroy_missile_in_range(dist, safe_destroy_dist=1500)
                    if safe_destroy:  # definitive, no need for asserting test, always destroy missile
                        # missile self destroy on safe distance, notify target player, release control
                        keep_control = False  # release missile control
                        release_reason = MissileControlRelease.SAFE_DISTANCE
                        break

                    # if pos and target exist, then  safe_destroy should not be None
                    safe_missile_speed = self.safe_missile_speed(safe_msl_spd=250)
                    if self.assert_defeat_on_criteria(self.missile_defeat_spd, safe_missile_speed):
                        keep_control = False
                        release_reason = MissileControlRelease.OUT_MANEUVER
                        break

                    # even if missile still has high speed, has to pass app vector check
                    missile_bad_approach = self.check_missile_approach()
                    if missile_bad_approach is None:  # not enough data to assert, ignore
                        break

                    if self.assert_defeat_on_criteria(self.missile_defeat_app, missile_bad_approach):
                        keep_control = False
                        release_reason = MissileControlRelease.OUT_MANEUVER
                        break

                    break

            else:  # no target, or missile does not exist
                keep_control = False
                release_reason = MissileControlRelease.LOCK_BREAK

        if target and not keep_control:  # intend to release control
            self.control_release_reason = release_reason
            report_simulation_result(target, release_reason)

        return keep_control
