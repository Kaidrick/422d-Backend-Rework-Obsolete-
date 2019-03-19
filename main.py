# -- system
import time
import threading

# -- basic data mapping function
from core.essential.data_mapping import get_all_players_data, map_playable_group_info

# -- player preferences
from core.request.api.player_preference import get_player_preference_settings

# -- from Export.lua
from core.request.exp.export_data import RequestExportUnitsData

# -- process api pulls and miz pull
from core.request.api.api_pull import process_api_pulls
from core.request.miz.dcs_pull import process_pulls

# -- load plugins
from plugins import *
import plugins.declare_plugins as dp

# -- testing
import core.data_interface as cdi
from core.request.miz.dcs_debug import RequestDcsDebugCommand


def step():
    """
    Main step method. Runs every 0.1 seconds. Used to retrieve data from Mission Env
    :return:
    """
    while True:
        get_all_players_data()
        time.sleep(0.1)


def prec_step():
    """
    Precision step method. Runs every 0.01 seconds. Used to retrieve position and attitude data from Export.lua
    :return:
    """
    while True:
        res = RequestExportUnitsData().send()

        for object_runtime_id_name, object_data in res.items():

            if object_data['Flags']['Human'] is True:
                unit_type = object_data['Name']
                player_name = object_data['UnitName']
                group_name = object_data['GroupName'].lstrip(' ').rstrip(' ')

                lop = cdi.playable_unit_info_by_group_name[group_name]  # FIXME: either group name or group id is WRONG
                p_group_id = cdi.group_id_alloc_by_player_name[player_name]
                print(f"sending to {p_group_id} {object_runtime_id_name}")
                RequestDcsDebugCommand(f"trigger.action.outTextForGroup({p_group_id}, "
                                       f"'track: {time.time()}', 1, true)").send()
                # print(object_runtime_id_name, unit_type, player_name, group_name)
                # id_16938241
                # res_test = {
                #     'Heading': 5.412256360054,
                #     'Bank': -0.00099762040190399,
                #     'Pitch': 0.091638997197151,
                #     'Position': {'x': -399128.69931336, 'y': 563.55842578656, 'z': -18581.799532482},
                #     'LatLongAlt': {
                #         'Alt': 563.55842578656, 'Lat': 36.227060267933, 'Long': -115.048208364
                #     },
                #     'Coalition': 'Enemies',
                #     'CoalitionID': 2,
                #     'Country': 2,
                #
                #     'Flags': {
                #         'AI_ON': True, 'Born': True, 'Human': True, 'IRJamming': False, 'Invisible': False,
                #         'Jamming': False, 'RadarActive': False, 'Static': False
                #     },
                #
                #     'GroupName': 'AV-8B N/A (401) Sn: N/A',
                #     'Name': 'AV8BNA',
                #     'Type': {
                #          'level1': 1, 'level2': 1, 'level3': 1, 'level4': 260
                #     },
                #     'UnitName': 'Kaidrick'
                # }

        time.sleep(1)


def pull_loop():
    """
    Pull step. Runs every 0.1 seconds. Used to pull data from server. Does not have to be very frequent
    :return:
    """
    while True:
        process_api_pulls()
        process_pulls()

        get_player_preference_settings()

        time.sleep(0.1)


if __name__ == '__main__':
    map_playable_group_info()

    threading.Thread(target=step).start()
    threading.Thread(target=pull_loop).start()
    threading.Thread(target=prec_step).start()

    dp.load_plugins()
