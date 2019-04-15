import numpy as np
from core.request.miz.dcs_message import RequestDcsMessageForGroup
import core.data_interface as cdi
import core.utility.utils as utils
import core.utility.data_parsing
import core.utility.dcs as dcs
import core.utility.system_of_measurement_conversion as conv
from core.aircraft_type_system_of_measurement import get_aircraft_system
import gettext
from core.request.miz.dcs_env import set_msg_locale
from .data_interface import missiles_in_control, recent_missiles, \
    missile_training_range, incoming_missiles_by_target_id_name
from core.essential.player import Player


_ = gettext.gettext


def unit_object_by_runtime_id_name(runtime_id_name):
    for name, unit_obj in {**cdi.active_players_by_name, **cdi.other_units_by_name}.items():
        if unit_obj.runtime_id_name == runtime_id_name:
            return unit_obj

    # after search, none found
    return None


class MissileControlRelease:
    SAFE_DISTANCE = 0  # within safe distance
    OUT_MANEUVER = 1  # missile energy low(low speed or approach vector fail)
    LOCK_BREAK = 2  # radar lock broken
    DECOY = 3  # false target lock DCS Limitation: All missile can only have one target
    OUT_OF_RANGE = 4


# when player is in a ECS training range and a missile has been launched, send notice
# use a timer to get all missile and its target and tracking
# for each missile, get its current target
# Only send to player who is being targeted, only send missiles that is targeting this player.
def placeholder_name_for_this_report_function():
    # check current missiles
    target_missiles_dict = {}
    for missile_id_name, missile_object in missiles_in_control.items():
        kn_tgt = missile_object.current_target
        print("missile target is ", kn_tgt)
        if kn_tgt and type(kn_tgt) is Player:  # target is not None, and target is a Player object
            try:
                target_missiles_dict[kn_tgt.runtime_id_name].append(missile_object)
            except KeyError:  # this target is not in the dict, so create new dict
                target_missiles_dict[kn_tgt.runtime_id_name] = []
                target_missiles_dict[kn_tgt.runtime_id_name].append(missile_object)

    # after adding missiles to each player
    # table example:
    # Electronic Warfare Simulation
    # ————————————————————————————————
    # Status        Bearing     Range       Missile ID      Note
    # Tracking      351         37          12958373
    # Defeated      NaN         NaN         12938572        Energy Depleted
    # Defeated      NaN         NaN         21256434        Radar Lost Track
    # """
    for target_id_name, missile_object_list in target_missiles_dict.items():
        report_tbl = generate_simulation_report_table(target_id_name, missile_object_list)
        target_group_id = unit_object_by_runtime_id_name(target_id_name).group_id
        RequestDcsMessageForGroup(target_group_id, report_tbl, clearview=True).send()


def generate_simulation_report_table(target_runtime_id, missile_list):
    target = unit_object_by_runtime_id_name(target_runtime_id)
    missiles = missile_list
    target_lang = target.language
    _ = set_msg_locale(target_lang, "missile_training_announcer")
    # labels
    tbl = _("Electronic Warfare Simulation") + "\n" + \
        "——————————————————————————————————————————————" + "\n" + \
        _("Status") + "\t\t" + \
        _("Bearing") + "\t\t" + \
        _("Range") + "\t\t" + \
        _("Missile ID") + "\t\t" + \
        _("Note")
    # need to check both alive missiles and dead missiles
    # incoming_missiles_by_target_id_name / recent_missiles

    target_pos_nc = dcs.get_pos_north_correction(target.unit_pos)  # north correction at target pos
    for missile in missiles:  # for each alive missiles
        # if it's a "in control" missile, it must be tracking # TODO: other missiles other than SAM
        if not missile.launch_noticed:
            trk_sts = _("Launch")
            missile.launch_noticed = True
        else:  # has been notified once
            trk_sts = _("Tracking")
        # bearing, range --> need to know target location, missile location
        target_pos_array = utils.pos_to_np_array(target.unit_pos)
        missile_pos_array = utils.pos_to_np_array(missile.current_pos)
        hdg_vector = missile_pos_array - target_pos_array  # vector from target pos to missile pos
        mag_hdg = dcs.get_mag_hdg_by_vector(hdg_vector, target.unit_pos, target_pos_nc)
        hdg_disp = f"{np.rad2deg(mag_hdg):03.0f}"
        # get distance
        try:
            dist = f"{missile.distance_to_target:.0f}" + _(" m")
        except AttributeError:  # no such attribute, probably because new type of missile other than SAM
            dist = "NaN"

        msl_report = trk_sts + "\t\t" + hdg_disp + "\t\t" + \
            dist + "\t\t" + str(missile.wpn_object_id) + "\t\t" + \
            missile.weapon_data['desc']['typeName']

        tbl += "\n" + msl_report

    # tbl for defeated missile, note that defeated missiles has different dict structure
    for missile_id_name, missile_dt_dict in recent_missiles.items():
        # check old target, check current target
        # TODO: need to revisit this when working with aim120
        dead_missile = missile_dt_dict['missile_data']
        if dead_missile.current_target is target:
            release_reason = dead_missile.control_release_reason
            if release_reason == MissileControlRelease.SAFE_DISTANCE:
                trk_sts = _("Hit") + "\t\t"
                note = _("Splash Target")
            else:
                trk_sts = _("Defeated")
                if release_reason == MissileControlRelease.LOCK_BREAK:
                    note = _("Guidance Failed")
                elif release_reason == MissileControlRelease.OUT_MANEUVER:
                    note = _("Energy Depleted")
                else:  # TODO: other reason, revisit when the game can handle it
                    note = _("Other Reasons")

            hdg_disp = "NaN"
            dist = "NaN" + "\t"
            msl_report = trk_sts + "\t\t" + hdg_disp + "\t\t" + \
                dist + "\t\t" + str(dead_missile.wpn_object_id) + "\t\t" + \
                note

            tbl += "\n" + msl_report

    return tbl  # tbl string


# TODO: use an information integrated message to send to group rather than discrete message
def announce_simulation_launch(event_data, target):  # TODO: finish launcher announce and locale
    target_preference = target.preferred_system

    missile_launch_pos = event_data['weapon_data']['vector_data']['p']
    launcher_type = event_data['initiator_type']
    launcher_desc = event_data['weapon_data']['desc']['typeName']

    target_pos_array = utils.pos_to_np_array(target.unit_pos)
    launch_pos_array = utils.pos_to_np_array(missile_launch_pos)

    vector_to_missile = launch_pos_array - target_pos_array  # from target to missile pos @ t0
    launch_dist = float(np.linalg.norm(vector_to_missile))  # in meters

    launch_mag_bearing = dcs.get_mag_hdg_by_vector(vector_to_missile, target.unit_pos)
    launch_mag_bearing = np.rad2deg(launch_mag_bearing)

    _ = set_msg_locale(target.language, "missile_training_announcer")
    # unit based on target player preference
    if target_preference == 'mixed':
        target_preference = get_aircraft_system(target.unit_type)

    if target_preference == 'imperial':
        msg = ("Missile Launch: ") + launcher_desc + "\t" + \
            _("HDG ") + f"{launch_mag_bearing:03.0f}" + _(" for ") + \
            f"{conv.meters2nm(launch_dist):.0f}" + _(" nm")  # need to add launcher type as well
    elif target_preference == 'metric':
        msg = _("Missile Launch: ") + launcher_desc + "\t" + \
            _("HDG ") + f"{launch_mag_bearing:03.0f}" + _(" for ") + \
            f"{conv.meters2km(launch_dist):.0f}" + _(" km")  # need to add launcher type as well
    else:  # 'all'
        msg = _("Missile Launch: ") + launcher_desc + "\t" + \
              _("HDG ") + f"{launch_mag_bearing:03.0f}" + _(" for ") + \
              f"{conv.meters2nm(launch_dist):.0f}" + _(" nm") + _(" or ") + \
              f"{conv.meters2km(launch_dist):.0f}" + _(" km")  # need to add launcher type as well

    RequestDcsMessageForGroup(target.group_id, msg).send()


def report_simulation_result(target, release_reason):
    target_group_id = target.group_id
    msg = ""
    if MissileControlRelease.OUT_MANEUVER == release_reason:
        msg = _("Missile energy depleted!")
    elif MissileControlRelease.DECOY == release_reason:
        msg = _("Missile decoyed!")
    elif MissileControlRelease.LOCK_BREAK == release_reason:
        msg = _("Missile Lock Failed!")
    elif MissileControlRelease.SAFE_DISTANCE == release_reason:
        msg = _("Missile Hit!")

    RequestDcsMessageForGroup(target_group_id, msg).send()
