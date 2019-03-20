# -- system
import time
import threading

# -- basic data mapping function
from core.essential.data_mapping import get_all_players_data, map_playable_group_info, \
    get_all_groups_data, get_all_statics_data, group_data_process

# -- player preferences
from core.request.api.player_preference import get_player_preference_settings

# -- from Export.lua
# FIXME: deemed not reliable. Avoid at all cost.

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
        # get_all_players_data()
        time.sleep(0.1)


def prec_step():
    """
    Precision step method. Runs every 0.01 seconds. Used to retrieve position and attitude data from Export.lua
    :return:
    """
    while True:
        # get_all_players_data()
        res_group = get_all_groups_data()
        # res_static = get_all_statics_data()
        # print(res_static)

        # group_data_process(res_group)
        # res = RequestExportUnitsData().send()
        # FIXME: object runtime id from Export.lua is not reliable. Avoid using Export.lua at all



        # other_data_process(res)
        time.sleep(0.1)


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

    # threading.Thread(target=step).start()
    threading.Thread(target=pull_loop).start()
    threading.Thread(target=prec_step).start()

    dp.load_plugins()
