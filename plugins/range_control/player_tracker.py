# detect if player is in the range at the moment
# check if player is in range
from core.request.miz import dcs_env as db
import threading
import time
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import core.data_interface as cdi
from plugins.range_control.obsolete.weapon_delivery_evaluation import select_batch, select_weapon_data_entry_by_group_id, \
    evaluate_dt
from core.request.miz.dcs_message import RequestDcsMessageForGroup
from core.spark import SparkHandler


plugin_name = "Range Control"


weapon_tracking_range = [
    'R-61A', 'R-61B',
    'R-62A', 'R-62B',
    'R-74B',
    'R-76'
]

group_range_dict = {}
group_tracker_dict = {}

group_ammo = {}

# record player's ammo when player enters the range?


def record_group_ammo(group_id):  # FIXME get group ammo from miz env query
    ammos = db.env_group_dict[group_id].lead['ammo']
    group_ammo = []
    for ammo in ammos:
        if ammo['category'] == 0:  # shells
            pass
    print(ammo)


def find_group_in_range(group_id):
    range_id = 666
    return range_id


def update_group_range_pos(group_id):
    """if player is no longer in range"""
    while True:
        # check if player is still in range
        # if player is in a tracking range
        try:
            p_as = cdi.active_players_by_group_id[group_id].get_airspace()
            # print(p_as)
        except KeyError:  # player unit no longer exists
            print(f"{group_id} no longer exists")
            break
        else:
            if p_as in weapon_tracking_range:
                # print(p_as)
                pass
            else:  # player is not in a tracking range
                print(f"Group {group_id} is no longer in a tracking range. Select batch and push data.")
                # if batch data is final, send data
                group_weapon_data = select_weapon_data_entry_by_group_id(group_id)
                group_batch = select_batch(group_weapon_data)

                # check if all batch data are final
                batch_final = True
                for batch in group_batch:
                    for dt in batch:
                        batch_final = batch_final and dt.cycle

                # if at the end of the loop batch is not final then postpone report until next iteration
                if batch_final:  # report
                    evaluation = evaluate_dt(group_batch, group_id)
                    RequestDcsMessageForGroup(group_id, evaluation).send()

                    break  # data report complete, break the while loop, end thread
                else:  # contains at least one tracker that is not final, postponed report
                    print(f"not final")

                # elif batch data is not final, wait until final

                # TODO: when to select batch and push data, sanitize dict after batch? record data?
                # select batch when leave range, push data when all weapon tracker final
                #       after weapon hit and player leaves range?
                # TODO: what if player left the range before weapon hit?
                # TODO: what if player

        # if group_in_range(group_id, range_id):
        #     # print(f"Group {group_id} is in {range_id}")
        #     pass
        # else:  # no longer in range
        #

        time.sleep(3)

    del group_tracker_dict[group_id]
    print(f"Tracker for Group {group_id} ends.")


# track player position on active weapon  --> keep one thread alive to tracking if active weapon
# if player in range then start to track
# if player not in range ignore
# when player leaves range report?
def check_active_weapon():
    acw = cdi.active_player_weapons
    for group_id, group_weapon_data in acw.items():  # check if group_weapon_data is empty:
        if group_weapon_data:
            # there is active weapon
            # is player in a range?
            # print(f"active weapon for group {group_id}")  # TODO: temporarily disable print for debug, because landing with ammunitions will force export
            # for range_name, range_dt in range_polygon.items():  # for each range, check if group pos is in

            # this might fail because, the weapon is still flying but launcher is already dead
            try:
                p_as = cdi.active_players_by_group_id[group_id].get_airspace()
            except KeyError:
                # group_id is not in

                # temporarily mute this output
                # print(__file__, "def check_active_weapon", f"{group_id} no longer exists")
                pass
            else:
                if p_as in weapon_tracking_range:
                    # player is in this range
                    if group_id not in group_tracker_dict.keys():
                        # start a tracker thread to track if player is still in the range
                        tracking_thread = threading.Thread(target=update_group_range_pos, args=[group_id])
                        group_tracker_dict[group_id] = tracking_thread
                        group_tracker_dict[group_id].start()
                    else:  # group_id is in dict
                        if group_tracker_dict[group_id]:
                            # print("tracker is already working. do nothing.")
                            pass

                # if group_in_range(group_id, range_name):
                #     # player is in this range
                #     if group_id not in group_tracker_dict.keys():
                #         # start a tracker thread to track if player is still in the range
                #         tracking_thread = threading.Thread(target=update_group_range_pos, args=[group_id, range_name])
                #         group_tracker_dict[group_id] = tracking_thread
                #         group_tracker_dict[group_id].start()
                #     else:  # group_id is in dict
                #         if group_tracker_dict[group_id]:
                #             # print("tracker is already working. do nothing.")
                #             pass


def run_player_tracker():
    while True:
        check_active_weapon()

        time.sleep(1)


def declare():
    pass
