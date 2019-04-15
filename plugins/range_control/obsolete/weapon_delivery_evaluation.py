from core.request.miz import dcs_env as db
import core.data_interface as cdi
from core.request.miz.dcs_navigation import generate_ll_deg_min
import time
import os
import json
import numpy as np
import scipy.spatial.distance
import gettext
from core.request.miz.dcs_debug import RequestDcsDebugCommand
from plugins.declare_plugins import plugin_log
from core.request.miz.dcs_env import set_msg_locale
from core.spark import SparkHandler
import threading

_ = gettext.gettext

player_eval_record = {}  # indexed by player name, contains data of whether a weapon has been reported to player
player_last_launch_timestamp = {}
player_last_term_timestamp = {}


def create_player_record(spk_dt):
    player_name = spk_dt['data']['name']
    player_eval_record[player_name] = []  # list that contains weapon object that has been evaluated

    player_last_launch_timestamp[player_name] = None
    player_last_term_timestamp[player_name] = None


def erase_player_record(spk_dt):  # erase record when player is not longer active
    player_name = spk_dt['data']['name']
    del player_eval_record[player_name]
    del player_last_launch_timestamp
    del player_last_term_timestamp[player_name]


def set_launch_timestamp(spk_dt):
    wpn_obj = spk_dt['data']['self']
    launcher_obj = wpn_obj.launcher
    try:
        player_name = launcher_obj.player_name
    except AttributeError:
        pass
    else:
        player_last_launch_timestamp[player_name] = wpn_obj.launch_time


SparkHandler.PLAYER_SPAWN['range_control_player_record_create'] = create_player_record
SparkHandler.PLAYER_DESPAWN['range_control_player_record_erase'] = erase_player_record
SparkHandler.WEAPON_RELEASE['range_control_record_player_launch_timestamp'] = set_launch_timestamp


def check_eval_criteria(launcher_obj):
    # this thread is spawn after a weapon is terminal, c1 is go

    # check cdi.active_munition to find all active weapon of this player
    for wpn_id_name, wpn_dt in cdi.active_munition.items():
        # get launcher
        kn_launcher = wpn_dt.launcher
        if launcher_obj is kn_launcher:  # this launcher still has at least one active weapon, eval NO GO
            return  # do nothing

    # after search and no match --> no active weapon
    ref_last_launch_timestamp = player_last_launch_timestamp[launcher_obj.player_name]
    time.sleep(10)  # wait 10 seconds and then check last launch time, use current time
    try:
        check_last_launch_timestamp = player_last_launch_timestamp[launcher_obj.player_name]
    except KeyError:
        print(__file__, "player no longer exists in the mission, ignore")
    else:
        if check_last_launch_timestamp == ref_last_launch_timestamp:  # this value does not change, no launch occurs
            print(f"do eval and push report data to player {launcher_obj.player_name}")


# TODO: send eval only if:
# TODO: 1. a player's weapon is terminal --> triggered by this, default GO
# TODO: 2. there is no other active munition deployed by this player --> check this immediately
# TODO: 3. no weapon is launched during the next 10 seconds --> check last launch timestamp


def player_weapon_terminal_recorder(spk_dt):  # trigger on weapon terminal spark
    wpn_obj = spk_dt['data']['self']
    launcher_obj = wpn_obj.launcher
    try:
        player_name = launcher_obj.player_name
    except AttributeError:  # not launched by a player
        print(__file__, "not launched by a player, ignore")
    else:
        player_last_term_timestamp[player_name] = wpn_obj.timestamp[-1]  # get last timestamp (terminal time)

        # spawn a new thread to check if last term timestamp changed after 10 seconds
        threading.Thread(target=check_eval_criteria, args=launcher_obj)


batch_interval = 5  # seconds
weapon_release_data = []
launcher_id_and_weapon_datum_dict = {}
batch_data = {}

# load warheads data
with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                       '../..', 'data') + "/weapon_data/warheads.json", 'r') as f:
    warheads_data = json.load(f)


# TODO: do eval when a weapon release by player is terminal and within 10 seconds there is no other launch?
# TODO: do eval only after the last player weapon is terminal
# TODO: Every time a player's weapon is terminal, spawn a new thread that checks after 10 seconds for active weapon

# check if release data has new entries
# if new entries, check if player has launch multiple weapons
# recognize multiple weapons as a bunch? how? by launch time?

# check if active weapons, if active weapons then check if player in range
# def timer():
#     for player_group_id, player_active_wpns in cdi.active_player_weapons.items():
#         if player_active_wpns:  # is not empty, then start to track player?
#             # when to select_batch()? after player leave the range? after all player weapons hit? that is, no active weapons


def select_weapon_data_entry_by_group_id(group_id):
    sel_dt = []
    done_list = []
    for idx, datum in enumerate(weapon_release_data):
        if datum.launcher_group_id == group_id:  # then select data, append to new list
            sel_dt.append(datum)
            done_list.append(idx)

    # for idx in done_list:
    #     del weapon_release_data[idx]
    for dt in sel_dt:
        weapon_release_data.remove(dt)

    return sel_dt


def evaluate_dt(group_batch, locale):  # use group_id to find user user group language
    # group id might not be valid because unit is dead now and erazed from group
    lang = locale

    global _
    _ = set_msg_locale(lang, 'weapon_delivery_evaluation')

    msg = _("Evaluation of Weapon Delivery Effectiveness") + "\n"
    print("length of group_batch: ", len(group_batch))
    for idx, batch in enumerate(group_batch):  # each batch is a list containing one or multiple trackers
        batch_num = idx + 1
        delivery_num = len(batch)  # QTY
        weapon_type = batch[0].weapon_type.split('.')[-1].title()
        weapon_category = batch[0].weapon_category
        print("DT weapon category: ", weapon_category)

        hits = []
        all_targets = []
        batch_evaluation_str = ""

        # print(cdi.hit_events)  # FIXME reconstruct code --> hit event has no weapon data nor launcher data
        # use estimated impact point and flight time

        # customized information of different type of weapon?
        if weapon_category == 0:  # shell, ignore for the moment
            print("ignore shells")

        elif weapon_category == 1:  # missiles
            if delivery_num == 1:  # single delivery
                # unable to obtain hit information, use estimation according to dist to nearest targets
                # on fin()?
                # ---------------------------------------------------
                # initial speed, which is the launch aircraft speed --> get from event shot
                # terminal speed                                    --> estimate from last update
                # terminal angle                                    --> estimate from last update
                # actual flight distance (for missiles only)        --> estimate from all updates
                # impact point coord                                --> estimate from last update with getIP
                # impact point to target distance                   --> estimate and calculate
                # time of flight                                    --> estimate
                # ---------------------------------------------------
                # find possible hits --> find in hit_events --> look for nearest hit time and target position?

                # is the estimation reliable?

                s_dt = batch[0]  # select the first and only weapon tracker object in this batch

                for hit_data in cdi.hit_events:  # what about sub-munition?
                    # check if any object is hit by this weapon
                    if 'weapon_data' in hit_data.keys():  # if it is hit by a weapon
                        if 'object' in hit_data['weapon_data'].keys():  # if weapon data valid at the moment of impact
                            if hit_data['weapon_data']['object']['id_'] == s_dt.lua_object_id:
                                # this tracker weapon hit this target, get target name and hit location
                                hit = {
                                    'target': hit_data['target_data']['name'],
                                    'pos': hit_data['target_data']['pos']['p'],
                                    'hit_pos': hit_data['weapon_data']['vector_data']['p'],
                                    'term_vel': hit_data['weapon_data']['vel_data'],
                                }
                                hits.append(hit)

                                all_targets.append(hit_data['target_data']['name'])

                # ip_vec3 = s_dt.trajectory_precise_pos[-1]
                kn_wpn_id = s_dt.unit_id_name
                ip_vec3 = s_dt.query_ip_vec3
                prec_ip_vec3 = s_dt.trajectory_precise_pos[-1]

                ip_ll = s_dt.trajectory_precise_ll_coord[-1]
                # ip_mgrs = s_dt.trajectory_mgrs_coord[-1]
                ll = generate_ll_deg_min(ip_ll['Lat'], ip_ll['Long'], ip_ll['Alt'])
                # mgrs = generate_mgrs_std(ip_mgrs)  # TODO: not used
                # he_eff = evaluate_he_effect(weapon_type, 1, ip_vec3)

                # batch_evaluation_str = \
                #     f" | Dir: {s_dt.dis_init_hdg:03.0f}" \
                #     f" | Alt: {s_dt.dis_init_alt:.0f}m\n" \
                #     f"Flt Time: {s_dt.dis_tof:.2f}s" \
                #     f" | V₀: {s_dt.dis_init_spd:.0f} m/s" \
                #     f" | V⊿: {s_dt.dis_term_spd:.0f} m/s\n" \
                #     f"Impact: {ll[0]} {ll[1]} at {ll[2]}m \n" \
                #     + evaluate_he_effect(weapon_type, 1, ip_vec3)

                batch_evaluation_str = \
                    " | " + _("Dir: ") + f"{s_dt.dis_init_hdg:03.0f}" + \
                    " | " + _("Alt: ") + f"{s_dt.dis_init_alt:.0f}" + _("m") + "\n" + \
                    _("Flt Time: ") + f"{s_dt.dis_tof:.2f}" + _("s") + \
                    " | V₀: " + f"{s_dt.dis_init_spd:.0f}" + _("m/s") + \
                    f" | V⊿: {s_dt.dis_term_spd:.0f}" + _("m/s") + "\n" + \
                    _("Impact: ") + f"{ll[0]} {ll[1]}" + _(" at ") + f"{ll[2]}" + _("m") + "\n" \
                    + evaluate_he_effect(weapon_type, 1, ip_vec3, prec_ip_vec3, kn_wpn_id)

            else:  # delivery quantity is 2 or more
                # average impact point
                # for dt in batch:
                #     # for multiple weapon tracker in one batch, calculate release interval?
                #     # calculate average impact point

                # for dt in batch:

                # after checking all hit events for this batch
                # calculate average impact point?
                ips = []
                for dt in batch:
                    # ip_vec3 = dt.trajectory_precise_pos[-1]
                    ip_vec3 = dt.query_ip_vec3

                    ips.append(ip_vec3)
                    # check if this tracker weapon has any hit
                    for hit_data in cdi.hit_events:  # what about sub-munition?
                        # check if any object is hit by this weapon
                        if 'weapon_data' in hit_data.keys():  # if it is hit by a weapon
                            if 'object' in hit_data['weapon_data'].keys():  # if weapon data valid at the moment of impact
                                if hit_data['weapon_data']['object']['id_'] == dt.lua_object_id:
                                    # this tracker weapon hit this target, get target name and hit location
                                    hit = {
                                        'target': hit_data['target_data']['name'],
                                        'pos': hit_data['target_data']['pos']['p'],
                                        'hit_pos': hit_data['weapon_data']['vector_data']['p'],
                                        'term_vel': hit_data['weapon_data']['vel_data'],
                                    }
                                    hits.append(hit)

                                    all_targets.append(hit_data['target_data']['name'])
                # after checking all hit events for this batch
                # calculate average impact point?
                x = [ip['x'] for ip in ips]
                y = [ip['z'] for ip in ips]
                impact_center = (sum(x) / len(ips), sum(y) / len(ips))
                batch_evaluation_str = _("Average Impact Point: ") + f"{impact_center}\n"

        elif weapon_category == 2:  # rockets
            if delivery_num == 1:  # single delivery
                # unable to obtain hit information, use estimation according to dist to nearest targets
                # on fin()?
                # ---------------------------------------------------
                # initial speed, which is the launch aircraft speed --> get from event shot
                # terminal speed                                    --> estimate from last update
                # terminal angle                                    --> estimate from last update
                # actual flight distance (for missiles only)        --> estimate from all updates
                # impact point coord                                --> estimate from last update with getIP
                # impact point to target distance                   --> estimate and calculate
                # time of flight                                    --> estimate
                # ---------------------------------------------------
                # find possible hits --> find in hit_events --> look for nearest hit time and target position?

                # is the estimation reliable?

                s_dt = batch[0]  # select the first and only weapon tracker object in this batch

                for hit_data in cdi.hit_events:  # what about sub-munition?
                    # check if any object is hit by this weapon
                    if 'weapon_data' in hit_data.keys():  # if it is hit by a weapon
                        if 'object' in hit_data['weapon_data'].keys():  # if weapon data valid at the moment of impact
                            if hit_data['weapon_data']['object']['id_'] == s_dt.lua_object_id:
                                # this tracker weapon hit this target, get target name and hit location
                                hit = {
                                    'target': hit_data['target_data']['name'],
                                    'pos': hit_data['target_data']['pos']['p'],
                                    'hit_pos': hit_data['weapon_data']['vector_data']['p'],
                                    'term_vel': hit_data['weapon_data']['vel_data'],
                                }
                                hits.append(hit)

                                all_targets.append(hit_data['target_data']['name'])

                # ip_vec3 = s_dt.trajectory_precise_pos[-1]  # probably not accurate enough?
                kn_wpn_id = s_dt.unit_id_name
                ip_vec3 = s_dt.query_ip_vec3
                prec_ip_vec3 = s_dt.trajectory_precise_pos[-1]
                # use last velocity to query intersection point?

                ip_ll = s_dt.trajectory_precise_ll_coord[-1]
                # ip_mgrs = s_dt.trajectory_mgrs_coord[-1]
                ll = generate_ll_deg_min(ip_ll['Lat'], ip_ll['Long'], ip_ll['Alt'])
                # mgrs = generate_mgrs_std(ip_mgrs)  # TODO: not used
                # he_eff = evaluate_he_effect(weapon_type, 1, ip_vec3)
                # batch_evaluation_str = \
                #     f" | Dir: {s_dt.dis_init_hdg:03.0f}" \
                #     f" | Alt: {s_dt.dis_init_alt:.0f}m\n" \
                #     f"Flt Time: {s_dt.dis_tof:.2f}s" \
                #     f" | V₀: {s_dt.dis_init_spd:.0f} m/s" \
                #     f" | V⊿: {s_dt.dis_term_spd:.0f} m/s\n" \
                #     f"Impact: {ll[0]} {ll[1]} at {ll[2]}m \n" \
                #     + evaluate_he_effect(weapon_type, 1, ip_vec3)

                batch_evaluation_str = \
                    " | " + _("Dir: ") + f"{s_dt.dis_init_hdg:03.0f}" + \
                    " | " + _("Alt: ") + f"{s_dt.dis_init_alt:.0f}" + _("m") + "\n" + \
                    _("Flt Time: ") + f"{s_dt.dis_tof:.2f}" + _("s") + \
                    " | V₀: " + f"{s_dt.dis_init_spd:.0f}" + _("m/s") + \
                    f" | V⊿: {s_dt.dis_term_spd:.0f}" + _("m/s") + "\n" + \
                    _("Impact: ") + f"{ll[0]} {ll[1]}" + _(" at ") + f"{ll[2]}" + _("m") + "\n" \
                    + evaluate_he_effect(weapon_type, 1, ip_vec3, prec_ip_vec3, kn_wpn_id)

            else:  # delivery quantity is 2 or more
                # average impact point
                # for dt in batch:
                #     # for multiple weapon tracker in one batch, calculate release interval?
                #     # calculate average impact point

                # for dt in batch:

                # after checking all hit events for this batch
                # calculate average impact point?
                ips = []
                for dt in batch:
                    # ip_vec3 = dt.trajectory_precise_pos[-1]
                    ip_vec3 = dt.query_ip_vec3

                    ips.append(ip_vec3)
                    # check if this tracker weapon has any hit
                    for hit_data in cdi.hit_events:  # what about sub-munition?
                        # check if any object is hit by this weapon
                        if 'weapon_data' in hit_data.keys():  # if it is hit by a weapon
                            if 'object' in hit_data['weapon_data'].keys():  # if weapon data valid at the moment of impact
                                if hit_data['weapon_data']['object']['id_'] == dt.lua_object_id:
                                    # this tracker weapon hit this target, get target name and hit location
                                    hit = {
                                        'target': hit_data['target_data']['name'],
                                        'pos': hit_data['target_data']['pos']['p'],
                                        'hit_pos': hit_data['weapon_data']['vector_data']['p'],
                                        'term_vel': hit_data['weapon_data']['vel_data'],
                                    }
                                    hits.append(hit)

                                    all_targets.append(hit_data['target_data']['name'])
                # after checking all hit events for this batch
                # calculate average impact point?
                x = [ip['x'] for ip in ips]
                y = [ip['z'] for ip in ips]
                impact_center = (sum(x) / len(ips), sum(y) / len(ips))
                batch_evaluation_str = _("Average Impact Point: ") + f"{impact_center}\n"

        elif weapon_category == 3:  # bombs
            if delivery_num == 1:  # single bomb
                # initial speed
                # terminal speed
                # terminal angle
                # impact point to target distance
                # time of flight
                s_dt = batch[0]  # select the first and only weapon tracker object in this batch

                for hit_data in cdi.hit_events:  # what about sub-munition?
                    # check if any object is hit by this weapon
                    if 'weapon_data' in hit_data.keys():  # if it is hit by a weapon
                        if 'object' in hit_data['weapon_data'].keys():  # if weapon data valid at the moment of impact
                            if hit_data['weapon_data']['object']['id_'] == s_dt.lua_object_id:
                                # this tracker weapon hit this target, get target name and hit location
                                hit = {
                                    'target': hit_data['target_data']['name'],
                                    'pos': hit_data['target_data']['pos']['p'],
                                    'hit_pos': hit_data['weapon_data']['vector_data']['p'],
                                    'term_vel': hit_data['weapon_data']['vel_data'],
                                }
                                hits.append(hit)

                                all_targets.append(hit_data['target_data']['name'])

                # ip_vec3 = s_dt.trajectory_precise_pos[-1]
                kn_wpn_id = s_dt.unit_id_name
                ip_vec3 = s_dt.query_ip_vec3
                prec_ip_vec3 = s_dt.trajectory_precise_pos[-1]

                ip_ll = s_dt.trajectory_precise_ll_coord[-1]
                # ip_mgrs = s_dt.trajectory_mgrs_coord[-1]
                ll = generate_ll_deg_min(ip_ll['Lat'], ip_ll['Long'], ip_ll['Alt'])
                # mgrs = generate_mgrs_std(ip_mgrs)
                # he_eff = evaluate_he_effect(weapon_type, 1, ip_vec3)
                # batch_evaluation_str = \
                #     f" | Dir: {s_dt.dis_init_hdg:03.0f}" \
                #     f" | Alt: {s_dt.dis_init_alt:.0f}m\n" \
                #     f"Flt Time: {s_dt.dis_tof:.2f}s" \
                #     f" | V₀: {s_dt.dis_init_spd:.0f} m/s" \
                #     f" | V⊿: {s_dt.dis_term_spd:.0f} m/s\n" \
                #     f"Impact: {ll[0]} {ll[1]} at {ll[2]}m\n" \
                #     + evaluate_he_effect(weapon_type, 1, ip_vec3)

                batch_evaluation_str = \
                    " | " + _("Dir: ") + f"{s_dt.dis_init_hdg:03.0f}" + \
                    " | " + _("Alt: ") + f"{s_dt.dis_init_alt:.0f}" + _("m") + "\n" + \
                    _("Flt Time: ") + f"{s_dt.dis_tof:.2f}" + _("s") + \
                    " | V₀: " + f"{s_dt.dis_init_spd:.0f}" + _("m/s") + \
                    f" | V⊿: {s_dt.dis_term_spd:.0f}" + _("m/s") + "\n" + \
                    _("Impact: ") + f"{ll[0]} {ll[1]}" + _(" at ") + f"{ll[2]}" + _("m") + "\n" \
                    + evaluate_he_effect(weapon_type, 1, ip_vec3, prec_ip_vec3, kn_wpn_id)

            else:  # two or more bombs
                # average impact point
                ips = []
                for dt in batch:
                    # ip_vec3 = dt.trajectory_precise_pos[-1]
                    ip_vec3 = dt.query_ip_vec3

                    ips.append(ip_vec3)
                    # check if this tracker weapon has any hit
                    for hit_data in cdi.hit_events:  # what about sub-munition?
                        # check if any object is hit by this weapon
                        if 'weapon_data' in hit_data.keys():  # if it is hit by a weapon
                            if 'object' in hit_data['weapon_data'].keys():  # if weapon data valid at the moment of impact
                                if hit_data['weapon_data']['object']['id_'] == dt.lua_object_id:
                                    # this tracker weapon hit this target, get target name and hit location
                                    hit = {
                                        'target': hit_data['target_data']['name'],
                                        'pos': hit_data['target_data']['pos']['p'],
                                        'hit_pos': hit_data['weapon_data']['vector_data']['p'],
                                        'term_vel': hit_data['weapon_data']['vel_data'],
                                    }
                                    hits.append(hit)

                                    all_targets.append(hit_data['target_data']['name'])
                # after checking all hit events for this batch
                # calculate average impact point?
                x = [ip['x'] for ip in ips]
                y = [ip['z'] for ip in ips]
                impact_center = (sum(x) / len(ips), sum(y) / len(ips))
                batch_evaluation_str = _("Average Impact Point: ") + f"{impact_center}\n"

        # one weapon can be responsible for multiple hit
        # find number of unique targets hit by this batch of weapon
        target_set = set(all_targets)
        num_uniq_tgts = len(target_set)

        batch_msg = "——————————————————————————\n" + _("Delivery Batch") + " #" + f"{batch_num} - " + \
            _("Type: ") + f"{weapon_type}" + " | " + _("Qty: ") + f"{delivery_num}" + batch_evaluation_str + "\n"

        msg += batch_msg
    print(msg)
    return msg


def select_batch(sel_gp_dt):  # select batch from player's weapon release record (list of Weapon object)
    # if weapon object is already in range control record list, then ignore
    # else add to range control record list and continue

    # sort data by time? is this necessary? list in python 3 retains the order items are inserted in?
    # but the player stats release weapon list is only appended on terminal, so still need to sort on launch time
    selected_group_weapon_dt = sel_gp_dt
    selected_group_weapon_dt.sort(key=lambda x: x.launch_time, reverse=False)

    # selected_group_weapon_dt is a list
    group_batch_data = []  # this group's weapon batch

    data_size = len(selected_group_weapon_dt)
    print("data size: ", data_size)

    # take the first one, find all other valid data

    # check type, type next type equals to this type
    next_idx = 0
    previous_ni = 0
    eod = False
    while_loop_count = 0  #
    while not eod and data_size != 0:
        while_loop_count += 1
        batch = []
        wpn_type = selected_group_weapon_dt[next_idx].weapon_type
        rel_time = selected_group_weapon_dt[next_idx].launch_time

        previous_ni = next_idx

        # print("next_idx: ", next_idx, wpn_type, rel_time)

        batch.append(selected_group_weapon_dt[next_idx])

        if data_size < 2:
            group_batch_data.append(batch)
            break  # this is the only data, break while loop

        for p_idx, p_data in enumerate(selected_group_weapon_dt[next_idx+1:]):
            # print(f"take selected_group_weapon_dt from {next_idx+1} to the end")
            # print(f"p_idx: {p_idx}, p_data.weapon_type == {p_data.weapon_type}")
            # print(f"next_idx + 1 + p_idx {next_idx + 1 + p_idx}")
            # if this for loop iterate to the last data
            if (next_idx + p_idx) == (data_size - 1):
                print("end of data")
                # eod = True
                group_batch_data.append(batch)
                break

            if p_data.weapon_type == wpn_type and p_data.launch_time - rel_time < batch_interval:
                batch.append(p_data)

            elif p_data.weapon_type != wpn_type:
                print("new batch because of weapon type")
                group_batch_data.append(batch)

                next_idx += (p_idx + 1)
                break  # break for loop
            elif p_data.launch_time - rel_time < batch_interval:
                print("new batch because of out of launch interval")
                group_batch_data.append(batch)

                next_idx += (p_idx + 1)
                break  # break for loop
            else:  # not same type or not in time interval
                print("new batch other reasons")
                group_batch_data.append(batch)

                next_idx += (p_idx + 1)
                break  # break for loop

        # only the last batch group will reach this line of code (last loop)
        # group_batch_data.append(batch)

        if next_idx == previous_ni:
            group_batch_data.append(batch)
            print(f"previous nix is {previous_ni}, next idx is {next_idx}. break")
            break

        time.sleep(1)

    print("while is looped", while_loop_count, "times")
    return group_batch_data


def evaluate_he_effect(wpn_type_name, surface_type_name, ip_vec3, prec_ip_vec3, wpn_id):  # pass group_ip?
    """
    generate evaluation string based on warhead type and its power and explosion effect size (visual?)
    :param ip_vec3: vec3 of the impact point, used for shock wave hit calculation
    :param wpn_type_name:
    :param surface_type_name
    :param prec_ip_vec3
    :param wpn_id: unit_id_name for this weapon, used to distinguish self from other units
    :return: expl_eff_str
    """
    shockwave_hit = 0
    effective_dmg_hit = 0
    bullseye_hit = False
    ip_array = np.array([ip_vec3['x'], ip_vec3['z']])
    prec_ip_array = np.array([prec_ip_vec3['x'], prec_ip_vec3['z']])

    # check different format? title, upper, lower, dash, underscore
    if wpn_type_name in warheads_data.keys():
        wpn_warhead_data = warheads_data[wpn_type_name]  # Mk_82, for example

    elif wpn_type_name.replace("-", "_") in warheads_data.keys():  # Aim-120 to Aim_120
        wpn_warhead_data = warheads_data[wpn_type_name.replace("-", "_")]

    elif wpn_type_name.upper() in warheads_data.keys():  # Aim-120C to AIM-120C
        wpn_warhead_data = warheads_data[wpn_type_name.upper()]

    elif wpn_type_name.upper().replace("-", "_") in warheads_data.keys():  # Aim-120C to AIM_120C
        wpn_warhead_data = warheads_data[wpn_type_name.upper().replace("-", "_")]

    else:  # no match
        wpn_warhead_data = warheads_data["Super_530D"]

    if 'expl_mass' not in wpn_warhead_data.keys():
        pass  # ignore warhead with no explosive mass, such as smoke rockets
    else:
        expl_mass = wpn_warhead_data['expl_mass']
        mass = wpn_warhead_data['mass']

        # concrete_factors = {HE1, HE2, HE3},
        # Factors of high-explosive action when getting into concrete:
        # HE1 - high explosive damaging effect (expl_mass * HE1)
        # HE2 - the size of the explosion effect
        # HE3 - size of the explosion funnel
        concrete_factors = wpn_warhead_data['concrete_factors']

        # penetrating factors when falling into concrete
        concrete_obj_factor = wpn_warhead_data['concrete_obj_factor']
        cumulative_factor = wpn_warhead_data['cumulative_factor']
        cumulative_thickness = wpn_warhead_data['cumulative_thickness']

        # obj_factors = {HE1, HE2},
        # The coefficient of high-explosive action when hitting a ground object (equipment):
        # HE1 - high explosive damaging effect (expl_mass * HE1)
        # HE2 - the size of the explosion effect
        obj_factors = wpn_warhead_data['obj_factors']

        # other_factors = {HE1, HE2, HE3};
        # Factors of high explosive action when hitting the ground:
        # HE1. - high explosive damaging effect (expl_mass * HE1)
        # HE2. - size of the explosion effect
        # HE3. - size of the explosion funnel
        other_factors = wpn_warhead_data['other_factors']

        piercing_mass = wpn_warhead_data['piercing_mass']

        expl_eff_str = _("Effectiveness: ")
        # if a bomb falls into the ground, then the high-explosive effect will be 10 * 0.9 = 9
        if surface_type_name == db.SurfaceType.LAND:
            he_power = expl_mass * other_factors[0]
            he_size = expl_mass * other_factors[1]  # supposedly
            # he_size_funnel = expl_mass * other_factors[2]
            eff_radius = he_explosive_threshold(he_power)

            all_units = {**cdi.export_units, **cdi.export_dead_units}  # merge live and dead units?

            for unit_id_name, unit_dt in all_units.items():  # maybe because the target is already dead?
                # print(unit_dt.unit_pos)
                if unit_id_name != wpn_id:  # cannot be self
                    pos_array = np.array([unit_dt.unit_pos['x'], unit_dt.unit_pos['z']])
                    dist_query = scipy.spatial.distance.euclidean(ip_array, pos_array)
                    dist_prec = scipy.spatial.distance.euclidean(prec_ip_array, pos_array)
                    if dist_query and dist_prec < 100:
                        print(unit_id_name, dist_query, dist_prec)

                    if dist_query <= eff_radius[1] or dist_prec <= eff_radius[1]:
                        # kmd = f"""
                        # trigger.action.smoke({{x = {pos_array[0]}, y = {unit_dt.unit_pos['y']}, z= {pos_array[1]}}}, 1)"""
                        # RequestDcsDebugCommand(kmd).send()
                        if dist_query <= eff_radius[2] or dist_prec <= eff_radius[2]:
                            if dist_query <= eff_radius[2] / 2 or dist_prec <= eff_radius[2] / 2:
                                bullseye_hit = True
                                effective_dmg_hit += 1
                            else:
                                effective_dmg_hit += 1
                        else:
                            shockwave_hit += 1

            #
            #
            # for group_id, group_data in db.env_group_dict.items():
            #     for unit in group_data.units:
            #         pos_array = np.array([unit['pos']['x'], unit['pos']['z']])
            #         dist = scipy.spatial.distance.euclidean(ip_array, pos_array)
            #         # print(dist)
            #         if dist <= eff_radius[1]:
            #             print(unit['name'], dist)
            #             kmd = f"""
            #             trigger.action.smoke({{x = {pos_array[0]}, y = {unit['pos']['y']}, z= {pos_array[1]}}}, 1)    """
            #             # RequestDcsDebugCommand(kmd).send()
            #             if dist <= eff_radius[2]:
            #                 if dist <= eff_radius[2] / 2:
            #                     bullseye_hit = True
            #                     effective_dmg_hit += 1
            #                 else:
            #                     effective_dmg_hit += 1
            #             else:
            #                 shockwave_hit += 1
            #
            # for obj_name, static_object in db.env_static_objects.items():
            #     pos_array = np.array([static_object.pos['x'], static_object.pos['z']])
            #     dist = scipy.spatial.distance.euclidean(ip_array, pos_array)
            #     # print(dist)
            #     if dist <= eff_radius[1]:
            #         print(static_object.name, dist)
            #         kmd = f"""
            #         trigger.action.smoke({{x = {pos_array[0]}, y = {static_object.pos['y']}, z= {pos_array[1]}}}, 1)    """
            #         # RequestDcsDebugCommand(kmd).send()
            #         if dist <= eff_radius[2]:
            #             if dist <= eff_radius[2] / 2:
            #                 bullseye_hit = True
            #                 effective_dmg_hit += 1
            #             else:
            #                 effective_dmg_hit += 1
            #         else:
            #             shockwave_hit += 1

            if bullseye_hit:
                expl_eff_str += _("Direct Hit on Target") + " | " + _("H.E. Pwr: ") + f"{he_power}" + " | " + \
                                _("R_shockwave: ") + f"{eff_radius[1]:.0f}\n" + \
                                _("Effective Hit(s): ") + f"{effective_dmg_hit}" + _(" hit(s)") + \
                                " | " + _("Shockwave: ") + f"{shockwave_hit}" + _(" hit(s)")
            else:
                expl_eff_str += _("H.E. Pwr: ") + f"{he_power}" + " | " + \
                                _("R_shockwave: ") + f"{eff_radius[1]:.0f}\n" + \
                                _("Effective Hit(s): ") + f"{effective_dmg_hit}" + _(" hit(s)") + \
                                " | " + _("Shockwave: ") + f"{shockwave_hit}" + _(" hit(s)")

        elif surface_type_name == db.SurfaceType.RUNWAY or surface_type_name == db.SurfaceType.ROAD:
            he_power = expl_mass * concrete_factors[0]
            he_size = expl_mass * concrete_factors[1]
            concrete_strike = expl_mass * concrete_obj_factor
        elif surface_type_name == "object":  # how to tell if direct hit on target? hit event?
            pass

        return expl_eff_str
        # if a bomb falls on a concrete object, then the high-explosive effect will be 10 * 0.8, plus an additional 3 * 10 = 30 concrete striking effect is transferred to this object
        # if the bomb gets into the car, then the high-explosive effect will be 10 * 0.5,
        #     plus an additional 5 * 10 = 50 cumulative damage effect is transferred to this object if the armor of the car is less than 5 cm.


def he_explosive_threshold(power_level):
    # 1, 5, 10, 15, 30
    # to dmg infantry: in 1 meter more than 0.1
    # to dmg infantry: in 5 meter more than 0.5
    # to dmg infantry: in 10 meter more than 1
    #                     15                2.5
    #                     20                 4
    #                     25                 7
    #                     30                10.5

    # to dmg soft tgt:    1                 0.7
    #                     5                2.8
    #                     10                 9
    #                     15                19
    #                     20                34.2
    #                     25                56.1
    #                     30                  86.2

    # to dmg armor tgt
    #                     10                 301
    #                     15                 633
    #                     20                 1094
    #                     25                 1837
    #                     30                 6836

    radius_inf = np.sqrt(power_level / (np.pi * 0.0035))
    radius_soft = np.sqrt(power_level / (np.pi * 0.029))
    radius_armor = np.sqrt(power_level / (np.pi * 0.9))

    if radius_inf >= 50:
        radius_inf = 50

    if radius_armor >= 50:
        radius_armor = 50

    if radius_soft >= 50:
        radius_soft = 50

    return [radius_inf, radius_soft, radius_armor]
    # to unarmored


if __name__ == '__main__':
    # print(evaluate_he_effect("Mk_82", 1))
    for warhead, data in warheads_data.items():
        if 'expl_mass' in data.keys():
            expl_mass = data['expl_mass']
            weighted_power = expl_mass * data['other_factors'][0]
            size = data['other_factors'][1]

            th = he_explosive_threshold(weighted_power)

            print(warhead, f"Explosive Mass: {expl_mass}\nEffective Damage Radius: {th[0]:.2f} {th[1]:.2f} {th[2]:.2f}")
            #     if data['other_factors'][1] != 1:
            #         print(warhead, data)
            # else:
            #     print(warhead)

# # wait until player leaves range then report data
# def select_batch():
#     """
#     For each data in weapon_release_data,
#     :return:
#     """
#     for datum in weapon_release_data:
#         launcher = datum.launcher_group_id
#         if launcher not in launcher_id_and_weapon_datum_dict.keys():
#             launcher_id_and_weapon_datum_dict[launcher] = []
#
#         launcher_id_and_weapon_datum_dict[launcher].append(datum)  # not sorted
#
#         # sort by time
#
#     for launcher, data_list in launcher_id_and_weapon_datum_dict.items():
#         data_list.sort(key=lambda x: x.launch_time, reverse=False)
#
#         # find batch? launcher --> batch_list = [batch_1, batch_2, batch_3, ... ]
#     # print("batch_data")
#
#
#     for launcher, data in launcher_id_and_weapon_datum_dict.items():
#         data_size = len(data)  # -1 ?
#         print(launcher, data_size)
#         # take the first one, find all other valid data
#
#         batch_data[launcher] = []
#
#         # check type, type next type equals to this type
#         next_idx = 0
#         previous_ni = 0
#         eod = False
#         while not eod:
#             batch = []
#             wpn_type = data[next_idx].weapon_type
#             rel_time = data[next_idx].launch_time
#
#             batch.append(data[next_idx])
#
#             if data_size < 2:
#                 batch_data[launcher].append(batch)
#                 break  # this is the only data, break while loop
#
#             for p_idx, p_data in enumerate(data[next_idx+1:]):
#                 # print(f"iteration starts from idx {next_idx+1}, current p_idx is {p_idx}")
#                 # print(f"check weapon type is {wpn_type}, current wpn type is {p_data.weapon_type}")
#                 # print(f"check launch time is {rel_time}, this time is {p_data.launch_time}")
#                 # print(f"dt = {p_data.launch_time - rel_time}, batch interval is {batch_interval}")
#                 if p_data.weapon_type == wpn_type and p_data.launch_time - rel_time < batch_interval:
#                     # within same batch as the ref
#                     # print("same batch")
#                     batch.append(p_data)
#
#                     # if this for loop iterate to the last data
#                     if (next_idx + 1 + p_idx) == (data_size - 1):
#                         # print("reach end of list, break!")
#                         eod = True
#                         batch_data[launcher].append(batch)
#
#                 elif p_data.weapon_type != wpn_type:
#                     print("new batch because of weapon type")
#                     batch_data[launcher].append(batch)
#
#                     next_idx += (p_idx + 1)
#                     break  # break for loop
#                 elif p_data.launch_time - rel_time < batch_interval:
#                     print("new batch because of out of launch interval")
#                     batch_data[launcher].append(batch)
#
#                     next_idx += (p_idx + 1)
#                     break  # break for loop
#                 else:  # not same type or not in time interval
#                     print("new batch other reasons")
#                     batch_data[launcher].append(batch)
#
#                     next_idx += (p_idx + 1)
#                     break  # break for loop
#
#             # print(f"next idx is {next_idx}")
#             if next_idx == previous_ni:
#                 # print("end of list, push batch")
#                 # batch_data[launcher].append(batch)
#                 break
#
#             time.sleep(1)
#
#     print(batch_data)
#     for group_id, all_batch in batch_data.items():
#         print(f"Launcher group is {group_id}")
#         # value is a list
#         batch_count = 0
#         for batch in all_batch:
#             batch_count += 1
#             print(f"this is batch {batch_count}")
#             for trdt in batch:
#                 print(trdt.launch_time, trdt.weapon_type)
