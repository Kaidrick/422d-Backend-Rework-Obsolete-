"""
This file implements weapon data parsing and mapping methods.
"""
import collections
import core.data_interface as cdi
import core.spark as spark
from .bomb import Bomb
from .rocket import Rocket
from .weapon import Weapon


filter_reference_wpn_data = {}
filter_watch_list = {}


def select_weapon_data(export_data):
    wpn_export_data = {}
    for unit_id_name, unit_data in export_data.items():
        unit_type = unit_data['Type']
        unit_name = unit_data['Name']
        if unit_type['level1'] == 4 and unit_name != "":  # wsType = 4, weapon
            wpn_export_data[unit_id_name] = unit_data  # assert weapon

    return wpn_export_data


def weapon_data_filter(wpn_export_data):
    """
    This method is used to filter invalid weapon export data.
    The reason why this is needed is that export data of a weapon (even though only bombs have been tested)
    will still remain in the export even if the weapon has been inactive in mission environment
    therefore, this method needs to check wpn_export_data for object position and attitude.
    First select wsType level 4 (weapon)
    :param wpn_export_data:
    :return:
    """
    # remove any obsolete entry from watch list, check if unit id name still exists in raw export data
    # if exist, then keep in watchlist
    # if not, it should have been removed naturally
    # ------------------------------------------------------
    global filter_watch_list
    global filter_reference_wpn_data

    edit_watchlist = filter_watch_list.copy()
    for unit_id_name in filter_watch_list.keys():
        if unit_id_name not in wpn_export_data.keys():
            del edit_watchlist[unit_id_name]

    filter_watch_list = edit_watchlist

    # -------------------------------------------------------

    valid_wpn_export_data = {}
    for unit_id_name, unit_data in wpn_export_data.items():
        try:
            ref_data = filter_reference_wpn_data[unit_id_name]
        except KeyError:  # unit_id_name not in reference, it should have been removed normally
            # remove
            print("pass")
            pass
        else:  # found ref_data
            if ref_data['Position'] == unit_data['Position']:
                # check if in watch list, but should still keep pushing data
                if unit_id_name not in filter_watch_list.keys():
                    filter_watch_list[unit_id_name] = {
                        'Position': collections.deque(maxlen=5)
                    }
                    filter_watch_list[unit_id_name]['Position'].append(ref_data['Position'])
                    valid_wpn_export_data[unit_id_name] = unit_data
                else:  # is already in watch list
                    # push data to this list
                    filter_watch_list[unit_id_name]['Position'].append(unit_data['Position'])

                    if len(filter_watch_list[unit_id_name]['Position']) == 5 and \
                       all(trj == filter_watch_list[unit_id_name]['Position'][0]
                           for trj in filter_watch_list[unit_id_name]['Position']):
                        # assert data freeze, invalid data
                        # print("filtered invalid weapon data: ", unit_id_name)
                        pass  # discard this entry
                    else:
                        valid_wpn_export_data[unit_id_name] = unit_data
            else:  # data is still flowing, this is valid data
                valid_wpn_export_data[unit_id_name] = unit_data

    filter_reference_wpn_data = wpn_export_data  # push this cycle of data to reference dict
    return valid_wpn_export_data


def weapon_data_process(export_timestamp):
    """
    This method process all weapon data in the export environment
    :param:
    :return:
    """

    # sel_dt = select_weapon_data({**cdi.export_ballistic, **cdi.export_units})  # current data
    sel_dt = select_weapon_data(cdi.export_omni)
    wpn_export_data = weapon_data_filter(sel_dt)
    # print(time.time(), wpn_export_data)

    # parse weapons (namely, missiles) here?
    wpn_omni = cdi.active_munition  # last cycle, used for triggering weapon terminal spark
    wpn_edit = {}  # new data

    active_weapon_id_names = cdi.active_munition.keys()

    check_weapon_id_names = []

    # find weapons from export unit data
    for unit_id_name, unit_data in wpn_export_data.items():
        # check wsType
        unit_type = unit_data['Type']
        if unit_id_name not in active_weapon_id_names:  # new name, create new weapon object
            if unit_type['level2'] == 4:  # missile
                kn_weapon = Rocket(unit_id_name, unit_data, export_timestamp)
            elif unit_type['level2'] == 5:  # Bomb
                kn_weapon = Bomb(unit_id_name, unit_data, export_timestamp)
            elif unit_type['level2'] == 6:  # Shell
                kn_weapon = Rocket(unit_id_name, unit_data, export_timestamp)
            elif unit_type['level2'] == 7:  # NURS (Rockets)
                kn_weapon = Rocket(unit_id_name, unit_data, export_timestamp)
            else:
                kn_weapon = Weapon(unit_id_name, unit_data, export_timestamp)
        else:  # name already exists, call update method
            kn_weapon = cdi.active_munition[unit_id_name].update(unit_data, export_timestamp)

        wpn_edit[unit_id_name] = kn_weapon  # new weapon or updated weapon
        check_weapon_id_names.append(unit_id_name)

    # after collecting loop, push data
    cdi.active_munition = wpn_edit

    # -- Weapon spark detection

    # FIXME: weapon going inactive only if data is the same
    # FIXME: use a deque to check for 10 consecutive position

    # assert weapon go inactive if weapon export data freezes or unit_id_name dropped from dictionary

    # # check if new unit spawn --> list does not contain unit name
    for check_name in check_weapon_id_names:
        if check_name not in active_weapon_id_names:  # new player spawn
            # trigger_spark_player_spawn(check_name, p_edit)
            # print("Weapon Going Active")
            trigger_spark_weapon_release(check_name, wpn_edit)
    #
    # # check if obsolete unit de-spawn -->
    for check_name in active_weapon_id_names:
        if check_name not in check_weapon_id_names:  # player de-spawn
            # trigger_spark_player_despawn(check_name, p_omni)
            # print("Weapon Going Inactive")  # export data cleared, can be deleted from cdi
            trigger_spark_weapon_terminal(check_name, wpn_omni)
        # else:  # check name is still in check_weapon_id_names, but validity should be checked
        #     if not cdi.active_munition[check_name].is_active():
        #         print("Weapon Going Inactive (Freeze)")


def trigger_spark_weapon_release(check_name, wpn_edit):
    kn_check = wpn_edit[check_name]
    spk_dt = {
        'type': 'weapon_release',
        'data': {
            'runtime_id': kn_check.wpn_id_name,
            'display_name': kn_check.display_name,
            'init_point': kn_check.init_pos,
            'init_ll': kn_check.init_ll,
        }
    }
    spark.weapon_release(spk_dt)
    # print(f"Weapon Release: {spk_dt['data']['runtime_id']}"
    #       f"({spk_dt['data']['display_name']}) at {spk_dt['data']['init_ll']}")


def trigger_spark_weapon_terminal(check_name, wpn_omni):
    kn_check = wpn_omni[check_name]
    spk_dt = {
        'type': 'weapon_terminal',
        'data': {
            'runtime_id': kn_check.wpn_id_name,
            'display_name': kn_check.display_name,
            'terminal_point': kn_check.trajectory[-1],
            'terminal_ll': kn_check.geo_coord[-1],
            'self': kn_check
        }
    }
    spark.weapon_terminal(spk_dt)
    # print(f"Weapon Terminal: {spk_dt['data']['runtime_id']}"
    #       f"({spk_dt['data']['display_name']}) at {spk_dt['data']['terminal_ll']}")


# -----------------------------------------------------------------------
def weapon_shot_logger(event_data):
    wpn_runtime_id = 'id_' + str(event_data['weapon_data']['object']['id_'])
    cdi.weapon_shot_event_log[wpn_runtime_id] = event_data['weapon_data']
