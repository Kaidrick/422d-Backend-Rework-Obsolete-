"""
This file implements the ability to plan a carrier's route
1. the carrier should switch direction if player is within range of carrier operation
2. the carrier should switch back to its original track if player leave range
3. the carrier should be able to follow its route indefinitely  <-- when at last waypoint push new mission?
"""
from core.game_object_control.mission import Mission
from core.game_object_control.dcs_group_control import build_point
from core.game_object_control.command import ActivateBeacon  # neccessary?
import configparser
import core.data_interface as cdi
import time
import threading
import os
from plugins.declare_plugins import plugin_log


plugin_name = "Carrier OP Utils"

carrier_type_name = ['Stennis', 'LHA_Tarawa', 'VINSON']
# read carrier config from the config file
cfg = configparser.ConfigParser()
cfg_file = 'carrier_unit.cfg'
# cfg_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', '/carrier_op_utils/') + 'carrier_unit.cfg'

cfg.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'carrier_unit.cfg'))

plugin_log(plugin_name, f"Read config from file '{cfg_file}'")

carrier_cfg_by_unit_name = {}  # use group name as id?


def carrier_to_wp(group_name, wp):
    # send miz to game object
    miz = Mission(group_name)  # the constructor actually takes a "group name" rather than group_id, need a fix?
    miz.add_route_point([wp])
    miz.send()


def load_carrier(carrier_cfg):
    unit_name = cfg[carrier_cfg]['Unit Name']
    tcn_chn = cfg[carrier_cfg]['Tacan Channel']  # might not exist for russian carrier
    tcn_ident = cfg[carrier_cfg]['Tacan Ident']
    icls_chn = cfg[carrier_cfg]['ICLS Channel']  # might not exist though
    cru_spd = cfg[carrier_cfg]['Cruise Speed']

    wps = []  # contains all waypoints
    for key in cfg[carrier_cfg]:
        # print(key.upper())

        if key.startswith('wp'):  # is a waypoint
            # print(key, cfg[carrier_cfg][key].split(','))
            wp = cfg[carrier_cfg][key].split(',')
            x = float(wp[0])
            y = float(wp[1])
            # build unit in-game waypoint here?
            t = build_point(x, y, "Turning Point", "Turning Point", alt=0, spd=cru_spd)
            wps.append(t)
            # all wp added
            carrier_cfg_by_unit_name[unit_name] = {
                'waypoints': wps,
                'unit_name': unit_name,
                'tcn_chn': tcn_chn,
                'tcn_ident': tcn_ident,
                'icls_chn': icls_chn,
                'spd': cru_spd
            }


def carrier_control(unit_name, carrier_unit_cfg):
    print(f"{unit_name} has {len(carrier_unit_cfg['waypoints'])} waypoints"
          f"\nTCN {carrier_unit_cfg['tcn_chn']} {carrier_unit_cfg['tcn_ident']}"
          f"\nICLS {carrier_unit_cfg['icls_chn']}")
    # generate mission here
    # first check if this unit exist in export units data
    # search export_units for this unit data? only need to do it once though?
    group_name = ""
    runtime_id_name = ""
    time.sleep(5)  # must have a built-in delay before accessing the export data
    # print(cdi.export_units.items())  # why is this empty?
    for unit_id_name, unit_data in cdi.export_units.items():
        try:
            print(unit_name, unit_data.unit_name)
            if unit_data.unit_name == unit_name:  # unit found, check group name
                print(unit_data.group_name)
                group_name = unit_data.group_name
                runtime_id_name = unit_id_name
                print(runtime_id_name)
                break  # break the search for loop
        except AttributeError:
            pass

    # print(group_name, runtime_id_name)
    # start at wp0, push wp1, check if at wp1, if at wp1 then push wp2 check if at wp2
    # check if at wp num is the last idx num, if so then push wp1
    next_wp_idx = 0
    route_length = len(carrier_unit_cfg['waypoints'])
    while True:  # wp start at 0
        # push next waypoint
        pos = cdi.export_units[runtime_id_name].unit_pos
        dx = abs(carrier_unit_cfg['waypoints'][next_wp_idx].x - pos['x'])
        dy = abs(carrier_unit_cfg['waypoints'][next_wp_idx].y - pos['z'])

        # print(dx, dy)
        if dx < 1000 and dy < 1000:  # in range, push next waypoint
            # what is the next waypoint? is current waypoint the last waypoint in the list?
            if next_wp_idx == route_length - 1:  # say, wp at 3, len is 4, 3 == 4 - 1
                # at the last wp, push first waypoint as next waypoint
                next_wp_idx = 0  # the first wp
            else:  # not the last wp
                next_wp_idx = next_wp_idx + 1

            print(f"Push Next WP: {next_wp_idx}")
            carrier_to_wp(group_name, carrier_unit_cfg['waypoints'][next_wp_idx])
        else:  # not in range, no need to push next wp
            pass

        time.sleep(15)


def include_carrier_op_utils():
    for carrier_cfg in cfg.sections():  # for each carrier in carrier config file
        print(carrier_cfg)
        load_carrier(carrier_cfg)

        # check how many way point the carrier group have?
        # why use this if you have 0 wp? are you fucking stupid or what?

    # after finishing read all carrier cfg data, apply generate mission for each group
    # find group conflict --> TODO
    for unit_name, carrier_unit_cfg in carrier_cfg_by_unit_name.items():
        # for each unit? start a new thread to control carrier
        threading.Thread(target=carrier_control, args=[unit_name, carrier_unit_cfg]).start()


if __name__ == '__main__':
    from core.functions.map_units import map_other_units
    from core.request.exp.export_data import RequestExportUnitsData

    units = RequestExportUnitsData().send()
    map_other_units(units)

    include_carrier_op_utils()



