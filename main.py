# -- system
import time
import threading

# -- basic data mapping function
from core.essential.data_mapping import map_playable_group_info, \
    get_all_groups_data, get_all_statics_data, group_data_process

from core.essential.precise_data import export_step

from core.request.miz.dcs_airbases import init_airbases

# -- chat command
from core.essential import chat_commands

# -- weapon data
from core.essential import weapons

# -- player preferences
from core.request.api.player_preference import get_player_preference_settings

# -- from Export.lua
# FIXME: deemed not reliable. Avoid at all cost.
# FIXME:

# -- process api pulls and miz pull
from core.request.api.api_pull import process_api_pulls
from core.request.miz.dcs_pull import process_pulls
from core.request.miz.dcs_event import process_miz_precise_timing_events

# -- load plugins
from plugins import *
import plugins.declare_plugins as dp

# -- testing
import core.data_interface as cdi
from core.request.miz.dcs_debug import RequestDcsDebugCommand


def export():
    """
    Main step method. Runs every 0.1 seconds. Used to retrieve data from Mission Env
    :return:
    """
    while True:
        export_step()
        # print(time.time())
        # time.sleep(1)


def miz():
    """
    Precision step method. Runs every 0.01 seconds. Used to retrieve position and attitude data from Export.lua
    :return:
    """
    while True:
        # get_all_players_data()
        res_group = get_all_groups_data()
        if res_group:
            group_data_process(res_group)
        else:
            print("query returns no data")

        process_pulls()
        process_miz_precise_timing_events()

        time.sleep(1)


def pull():
    """
    Pull step. Runs every 0.1 seconds. Used to pull data from server. Does not have to be very frequent
    :return:
    """
    while True:
        process_api_pulls()
        get_player_preference_settings()

        time.sleep(0.1)


if __name__ == '__main__':
    map_playable_group_info()
    init_airbases()

    threading.Thread(target=export).start()
    threading.Thread(target=pull).start()
    threading.Thread(target=miz).start()

    dp.load_plugins()
