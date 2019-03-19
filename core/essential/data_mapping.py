"""
This file implement the functionality of retrieve game data from Export.lua and Mission Env
then map these data to respective dictionaries
"""
import os
import core.data_interface as cdi
import core.spark as spark
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
        cmd = f.read()  # read whole lua script

    res = RequestAPINetDostring(cmd, echo_result=True).send()  # do script
    cdi.playable_unit_info_by_name = res  # container dictionary, indexed by unit name
    for unit_name, unit_info in res.items():
        cdi.playable_unit_info_by_group_id[unit_info['group_id']] = unit_info
        cdi.playable_unit_info_by_group_name[unit_info['group_name']] = unit_info


# get all players data from mission env
# this data is used to determine if a player is active or not
# compare player names to a list.
# if new names, then relevant players have spawned. if missing names, players have de-spawned.
def get_all_players_data():
    """
    This method is supposed to be run every 0.01 second or so.
    Since a player name is unique per server, those player names can be thrown into a set
    There are two sets: active set and check set. Check set is always the newest player name list
    while active set is a set of player who have been active (in mission) during the last iteration

    if a name is in check but is not in active, then this is a new name --> new player spawn
    if a name is in active but is not in check, then this is a obsolete name --> player has de-spawn

    there are multiple possibilities:
    1. there is no player in the mission, and a player joins
    2. there is at least a player in mission, and a player joins
    3. there is only one player in the mission, and this player leaves
    4. there is at least two players in the mission, and one of them leaves
    5. for some reason, all players leaves at once

    :return:
    """
    _check_players_name_set = set()

    with open(f_get_all_players_data, 'r') as f:
        cmd = f.read()  # read lua script

    res = RequestDcsDebugCommand(cmd, True).send()  # do script
    if res:  # that is, if there is at least one player that is active in game
        # print(res)
        for player_name, player_info in res.items():
            _check_players_name_set.add(player_name)  # add to set

        global _active_players_name_set

        # player spawn
        new_names = _check_players_name_set.difference(_active_players_name_set)  # name in check, but no in active
        for name in new_names:
            print(f"Player >>>{name}<<< has entered mission.")
            # trigger spawn signal here?
            try:
                player_unit_name = res[name]['unit_name'].rstrip(' ')
                player_group_id = cdi.playable_unit_info_by_name[player_unit_name]['group_id']
                player_runtime_id_name = res[name]['unit_runtime_id_name'].rstrip(' ')
                # player_runtime_id is a string start with id_, not a number
            except KeyError:
                print(res)
                print(cdi.playable_unit_info_by_name)
                print(cdi.playable_unit_info_by_group_id)
                print(cdi.playable_unit_info_by_group_name)
            else:
                # trigger signal here
                # RequestDcsDebugCommand(f"trigger.action.outTextForGroup({player_group_id}, 'Welcome!', 10)").send()
                spk_dt = {
                    'type': 'player_spawn',
                    'data': {
                        'name': name,
                        'group_id': player_group_id,
                        'unit_name': player_unit_name,
                        'runtime_id': player_runtime_id_name
                    }
                }
                spark.player_spawn(spk_dt)
                print(f"Player >>>{spk_dt['data']['name']}<<< has spawned. "
                      f"GroupID: {spk_dt['data']['group_id']}, "
                      f"RuntimeID: {spk_dt['data']['runtime_id']}. ")

        # player de-spawn
        # print("before save:" + str(_active_players_name_set))
        obs_names = _active_players_name_set.difference(_check_players_name_set)
        for name in obs_names:
            print(f"Player >>>{name}<<< has left the mission.")

        # pass current name set to active set
        _active_players_name_set = _check_players_name_set

    else:  # no player at the moment (in the newest iteration), but maybe all the player is leaving in this check
        _check_players_name_set = set()

        obs_names = _active_players_name_set.difference(_check_players_name_set)
        for name in obs_names:
            print(f"Player >>>{name}<<< has left the mission.")

        _active_players_name_set = _check_players_name_set


if __name__ == '__main__':
    map_playable_group_info()

    get_all_players_data()
