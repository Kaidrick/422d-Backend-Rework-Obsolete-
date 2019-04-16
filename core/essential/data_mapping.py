"""
This file implement the functionality of retrieve game data from Export.lua and Mission Env
then map these data to respective dictionaries
"""
import os
import core.data_interface as cdi
import core.spark as spark
from core.request.miz.dcs_debug import RequestDcsDebugCommand
from core.request.miz.dcs_query import RequestDcsAllGroups, RequestDcsAllStaticObjects
from core.request.api.api_debug import RequestAPINetDostring
from core.essential.other_unit import parse_other_unit
from core.essential.player import parse_player_unit
import time


f_map_playable_group_info = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'scripts', 'map_playable.lua')
f_get_all_players_data = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'scripts', 'get_all_players_data.lua')


_active_players_name_set = set()


# map all playable units
def map_playable_group_info():
    """
    This method is supposed to be run at mission start. It retrieves data via api request from mission env,
    and get all playable units in the mission.
    The info (group id, group name and unit name) is mapped to data interface

    cmd is a Lua script used to access such data. It is passed to SSE via RequestAPINetDostring.
    :return:
    """

    with open(f_map_playable_group_info, 'r') as f:
        cmd = f.read()  # read whole lua script

    res = RequestAPINetDostring(cmd, echo_result=True).send()  # do script
    cdi.playable_unit_info_by_unit_name = res  # container dictionary, indexed by unit name
    for unit_name, unit_info in res.items():
        cdi.playable_unit_info_by_group_id[unit_info['group_id']] = unit_info
        cdi.playable_unit_info_by_group_name[unit_info['group_name']] = unit_info


def get_all_groups_data():
    return RequestDcsAllGroups().send()


def get_all_statics_data():
    return RequestDcsAllStaticObjects().send()


def group_data_process(res_group):
    """
    This method process all group data in the mission environment
    :param res_group:
    :return:
    """
    p_omni = cdi.active_players_by_name
    o_omni = cdi.other_units_by_name

    p_edit = {}
    o_edit = {}

    active_player_names = cdi.active_players_by_name.keys()
    active_other_names = cdi.other_units_by_name.keys()

    check_player_names = []
    check_other_names = []
    # if this group is a player group, then call parse_player

    # if this group is a AI group, then call parse_other

    # FIXME: maybe a numeric name will cause some problem? say, 18.3K ? once a player named this joined

    for group_data in res_group:  # check each group
        for unit in group_data['units']:  # check units in each group

            # FIXME: The DCS API function getPlayerName() returns the name of the RIO
            # FIXME: and once the second player (RIO) enters the aircraft. It should return the name of the pilot.
            # FIXME: Furthermore, the getPlayerName() function returns an empty string once the RIO left.

            # So the problem is as follows:
            # 1. player name is not accurate --> check API occupied slot
            #                                if slot then get player name from hook
            #                                if slot2 then get RIO name from hook

            # need to check unit id from the start
            # check if this unit id is in net side ref dict
            # if it is in the ref dict, then find the matching name, and override player name
            # since rio should always (at least in theory) spawn after the pilot did,
            # ref dict will only keep pilot name

            # FIXME: the problem here is, getPlayerName() return is flawed, and should be ignored for player unit
            check_unit_id = unit['id']
            # this has to be used with plugin --> static playable aircraft --> need to move to essential instead
            # TODO: finish spark handler function for SLOT_CHANGE
            try:  # check if player_name is in any slot
                player_name = cdi.player_in_net_slot[check_unit_id]
            except KeyError:
                # either this is not a player unit, or slot dict has not been populated for some reason
                pass
            else:

                unit['player_name'] = player_name  # override false player name return by API function

            # FIXME: spark a player spawn when player left an unit???
            # spark because check_player_names has this name

            if unit['player_control']:  # if player control flag is True
                if unit['player_name'] != "":
                    # if player name is already in the name list
                    if unit['player_name'] in active_player_names:
                        kn_player = cdi.active_players_by_name[unit['player_name']].update(unit)
                    else:
                        kn_player = parse_player_unit(group_data['id'], group_data['name'], group_data['coalition'],
                                                      group_data['category'], unit)
                        if kn_player.player_name == "":
                            print("wtf? " + str(unit))

                    check_player_names.append(kn_player.player_name)
                    p_edit[kn_player.player_name] = kn_player

            else:  # if player control flag is False
                if unit['name'] != "":
                    if unit['name'] in active_other_names:
                        kn_other = cdi.other_units_by_name[unit['name']].update(unit)
                    else:
                        kn_other = parse_other_unit(group_data['id'], group_data['name'], group_data['coalition'],
                                                    group_data['category'], unit)

                    check_other_names.append(kn_other.unit_name)
                    o_edit[kn_other.unit_name] = kn_other

    # after loop, push data
    cdi.active_players_by_name = p_edit
    cdi.other_units_by_name = o_edit

    # -- Player spark detection
    # check if new unit spawn --> list does not contain unit name
    for check_name in check_player_names:
        if check_name not in active_player_names:  # new player spawn
            trigger_spark_player_spawn(check_name, p_edit)

    # check if obsolete unit de-spawn -->
    for check_name in active_player_names:
        if check_name not in check_player_names:  # player de-spawn
            trigger_spark_player_despawn(check_name, p_omni)

    # -- Other spark detection
    for check_name in check_other_names:
        if check_name not in active_other_names:  # new player spawn
            # print(check_name + " has spawned")
            trigger_spark_other_spawn(check_name, o_edit)

    for check_name in active_other_names:
        if check_name not in check_other_names:  # player de-spawn
            # print(check_name + " has de-spawned")
            # dead unit or removed unit; add to dead_other_units dictionary
            trigger_spark_other_despawn(check_name, o_omni)


def trigger_spark_other_despawn(check_name, o_omni):
    kn_check = o_omni[check_name]
    spk_dt = {
        'type': 'other_despawn',
        'data': {
            'unit_name': kn_check.unit_name,
            'unit_type': kn_check.unit_type,
            'runtime_id': kn_check.runtime_id,
            'self': kn_check
        }
    }
    spark.other_despawn(spk_dt)

    # add to destroyed unit dict indexed by runtime_id_name + time
    cdi.destroyed_other_units[kn_check.runtime_id_name + '_' + str(time.time())] = kn_check

    print(f"Unit >>>"
          f"{spk_dt['data']['unit_name']}({spk_dt['data']['unit_type']}"
          f" - {spk_dt['data']['runtime_id']})"
          f"<<< has de-spawned. ")


def trigger_spark_other_spawn(check_name, o_edit):
    kn_check = o_edit[check_name]
    spk_dt = {
        'type': 'other_spawn',
        'data': {
            'unit_name': kn_check.unit_name,
            'unit_type': kn_check.unit_type,
            'runtime_id': kn_check.runtime_id,
            'self': kn_check
        }
    }
    spark.other_spawn(spk_dt)
    print(f"Unit >>>"
          f"{spk_dt['data']['unit_name']}({spk_dt['data']['unit_type']}"
          f" - {spk_dt['data']['runtime_id']})"
          f"<<< has spawned. ")


def trigger_spark_player_despawn(check_name, p_omni):
    kn_check = p_omni[check_name]
    spk_dt = {
        'type': 'player_despawn',
        'data': {
            'name': kn_check.player_name,
            'group_id': kn_check.group_id,
            'unit_name': kn_check.unit_name,
            'runtime_id': kn_check.runtime_id
        }
    }
    spark.player_despawn(spk_dt)
    print(f"Player >>>{spk_dt['data']['name']}<<< has de-spawned. "
          f"Old GroupID: {spk_dt['data']['group_id']}, "
          f"Old RuntimeID: {spk_dt['data']['runtime_id']}. ")


def trigger_spark_player_spawn(check_name, p_edit):
    kn_check = p_edit[check_name]
    spk_dt = {
        'type': 'player_spawn',
        'data': {
            'name': kn_check.player_name,
            'group_id': kn_check.group_id,
            'unit_name': kn_check.unit_name,
            'runtime_id': kn_check.runtime_id
        }
    }
    spark.player_spawn(spk_dt)
    print(f"Player >>>{spk_dt['data']['name']}<<< has spawned. "
          f"GroupID: {spk_dt['data']['group_id']}, "
          f"RuntimeID: {spk_dt['data']['runtime_id']}. ")


if __name__ == '__main__':
    map_playable_group_info()

    # get_all_players_data()
