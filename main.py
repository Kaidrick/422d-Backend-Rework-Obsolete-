import time
import threading

from core.essential.data_mapping import get_all_players_data, map_playable_group_info

from core.request.api.api_pull import process_api_pulls

from plugins import *
import plugins.declare_plugins as dp


def step():
    while True:
        get_all_players_data()
        time.sleep(1)


def pull_loop():
    while True:
        process_api_pulls()
        time.sleep(0.1)


if __name__ == '__main__':
    map_playable_group_info()

    threading.Thread(target=step).start()
    threading.Thread(target=pull_loop).start()

    dp.load_plugins()
