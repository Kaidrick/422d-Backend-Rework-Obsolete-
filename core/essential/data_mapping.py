"""
This file implement the functionality of retrieve game data from Export.lua and Mission Env
then map these data to respective dictionaries
"""
import os
import core.data_interface as cdi
from core.request.miz.dcs_debug import RequestDcsDebugCommand
from core.request.api.api_debug import RequestAPINetDostring


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
        cmd = f.read()

    res = RequestAPINetDostring(cmd, echo_result=True).send()
    cdi.playable_unit_info_by_name = res
    for unit_name, unit_info in res.items():
        cdi.playable_unit_info_by_group_id[unit_info['group_id']] = unit_info
        cdi.playable_unit_info_by_group_name[unit_info['group_name']] = unit_info


# get all players data from mission env
# this data is used to determine if a player is active or not
# compare player names to a list.
# if new names, then relevant players have spawned. if missing names, players have de-spawned.
def get_all_players_data():
    _check_players_name_set = set()

    with open(f_get_all_players_data, 'r') as f:
        cmd = f.read()

    res = RequestDcsDebugCommand(cmd, True).send()
    if res:
        # print(res)
        for player_name, player_info in res.items():
            _check_players_name_set.add(player_name)  # add to set

        global _active_players_name_set

        # player spawn
        new_names = _check_players_name_set.difference(_active_players_name_set)  # name in check, but no in active
        for name in new_names:
            print(f"New Player --> {name} has entered mission")
            # trigger spawn signal here?
            player_unit_name = res[name]['unit_name']
            player_group_id = cdi.playable_unit_info_by_name[player_unit_name]['group_id']

            # trigger signal here
            RequestDcsDebugCommand(f"trigger.action.outTextForGroup({player_group_id}, 'Welcome!', 10)").send()

        # player de-spawn

        _active_players_name_set = _check_players_name_set

    else:  # no player at the moment
        _check_players_name_set = set()
        _active_players_name_set = _check_players_name_set


if __name__ == '__main__':
    map_playable_group_info()
    # print(cdi.playable_unit_info_by_group_name)
    # print(cdi.playable_unit_info_by_group_id)
    # print(cdi.playable_unit_info_by_name)

    get_all_players_data()
