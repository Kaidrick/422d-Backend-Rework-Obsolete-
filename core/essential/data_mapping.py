"""
This file implement the functionality of retrieve game data from Export.lua and Mission Env
then map these data to respective dictionaries
"""
import os
import core.data_interface as cdi
from core.request.miz.dcs_debug import RequestDcsDebugCommand
from core.request.api.api_debug import RequestAPINetDostring


# map all playable units
def map_playable_group_info():
    """
    This method is supposed to be run at mission start. It retrieves data via api request from mission env,
    and get all playable units in the mission.
    The info (group id, group name and unit name) is mapped to data interface

    cmd is a Lua script used to access such data. It is passed to SSE via RequestAPINetDostring.
    :return:
    """
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'scripts', 'map_playable.lua')
    with open(file_path, 'r') as f:
        cmd = f.read()

    res = RequestAPINetDostring(cmd, echo_result=True).send()
    cdi.playable_unit_info_by_name = res
    for unit_name, unit_info in res.items():
        cdi.playable_unit_info_by_group_id[unit_info['group_id']] = unit_info
        cdi.playable_unit_info_by_group_name[unit_info['group_name']] = unit_info


# get all players data from mission env


if __name__ == '__main__':
    map_playable_group_info()
    # print(cdi.playable_unit_info_by_group_name)
    # print(cdi.playable_unit_info_by_group_id)
    # print(cdi.playable_unit_info_by_name)
