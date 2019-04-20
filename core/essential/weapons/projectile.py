"""
This file implements data model for general purpose bomb and guided bomb
what about sub-munition you ask?
"""
import collections
import core.data_interface as cdi
import numpy as np
from .weapon import Weapon
import core.utility.data_parsing as parse


class Projectile(Weapon):
    def __init__(self, weapon_runtime_id, weapon_data, timestamp):
        super().__init__(weapon_runtime_id, weapon_data, timestamp)

    def find_launcher(self):
        t_check_pos = np.array([self.init_pos['x'], self.init_pos['y'], self.init_pos['z']])
        check_alt = self.init_pos['y']

        search_dict = {**cdi.active_players_by_name, **cdi.other_units_by_name}

        # check find the player or the other_unit who launched this weapon
        for name, launcher_object in search_dict.items():  # possible launcher object
            runtime_id_name = launcher_object.runtime_id_name
            # check if export data has a matching runtime_id_name
            if runtime_id_name not in cdi.export_omni.keys():
                # no matching runtime id, search for UnitName instead
                for s_rtid, s_dt in cdi.export_omni.items():
                    if 'UnitName' in s_dt.keys() and s_dt['UnitName'] == launcher_object.unit_name:
                        print("mismatched runtime id", launcher_object.unit_name, s_rtid)
                        launcher_dt = s_dt
                        break
                    else:  # cannot find UnitName in export data either, might be bad export data
                        return None
            else:  # there is a matching id, get this data
                launcher_dt = cdi.export_omni[runtime_id_name]

            launcher_pos = launcher_dt['Position']
            # launcher_pos = launcher_object.unit_pos
            launcher_move_dir = launcher_object.move_dir  # array
            t_launcher_pos = np.array([launcher_pos['x'], launcher_pos['y'], launcher_pos['z']])
            launcher_alt = launcher_pos['y']
            # check 3d distance between this player's pos and this current weapons position
            dist = np.linalg.norm(
                t_check_pos - t_launcher_pos)  # distance between weapon launch position and this A/C
            # print("wpn check dist: ", dist, "wpn check height: ", launcher_alt - check_alt)

            # FIXME: if no using hi res data, distance is sometimes too far for accurate assertion

            if 50 < dist < 600:
                array_wpn_init_pos = np.array([
                    self.init_pos['x'], self.init_pos['y'], self.init_pos['z']
                ])
                array_launcher_pos = np.array([
                    launcher_pos['x'], launcher_pos['y'], launcher_pos['z']
                ])
                array_wpn_launch_vector = array_wpn_init_pos - array_launcher_pos
                # check angle to move_dir
                angle = parse.angle_between(array_wpn_launch_vector, launcher_move_dir)
                if angle <= 20:
                    # print("launch br:", np.rad2deg(angle))
                    if name in cdi.active_players_by_name.keys():
                        return cdi.active_players_by_name[name]

                    if name in cdi.other_units_by_name.keys():
                        return cdi.other_units_by_name[name]

            #
            #
            # try:
            #
            #     launcher_dt = cdi.export_omni[runtime_id_name]  # error is launcher KeyError?
            # except KeyError as e:  # cannot find this id in export data, either data is wrong, or player is inactive
            #     # FIXME: WTF?????????????????????
            #     # so laggy that it's not in export_omni yet?
            #     # print("unit name is", launcher_object.unit_name, launcher_object.unit_type)
            #     # those units that cannot be found are refueling aircraft and ATIS soldier
            #     # those units are added to game dynamically. is this the reason?
            #
            #     # here is a guess
            #     # when a launcher can not be asserted, these units are iterated, which are never in the export list?
            #     # chances are that they do not share the same runtime_id as in the mission environment?
            #     # but what's the point?
            #     # maybe search by unit_name?
            #     for s_rtid, s_dt in cdi.export_omni.items():
            #         if 'UnitName' in s_dt.keys() and s_dt['UnitName'] == launcher_object.unit_name:
            #             print("mismatched runtime id", launcher_object.unit_name, s_rtid)
            #             launcher_dt = s_dt
            #             break
            #
            #     # if loop is finished --> not found
            #     print("id not in export data or data wrong or player is inactive", e)
            # else:
            #     launcher_pos = launcher_dt['Position']
            #     # launcher_pos = launcher_object.unit_pos
            #     launcher_move_dir = launcher_object.move_dir  # array
            #     t_launcher_pos = np.array([launcher_pos['x'], launcher_pos['y'], launcher_pos['z']])
            #     launcher_alt = launcher_pos['y']
            #     # check 3d distance between this player's pos and this current weapons position
            #     dist = np.linalg.norm(
            #         t_check_pos - t_launcher_pos)  # distance between weapon launch position and this A/C
            #     # print("wpn check dist: ", dist, "wpn check height: ", launcher_alt - check_alt)
            #
            #     # FIXME: if no using hi res data, distance is sometimes too far for accurate assertion
            #
            #     if 100 < dist < 300:
            #         array_wpn_init_pos = np.array([
            #             self.init_pos['x'], self.init_pos['y'], self.init_pos['z']
            #         ])
            #         array_launcher_pos = np.array([
            #             launcher_pos['x'], launcher_pos['y'], launcher_pos['z']
            #         ])
            #         array_wpn_launch_vector = array_wpn_init_pos - array_launcher_pos
            #         # check angle to move_dir
            #         angle = parse.angle_between(array_wpn_launch_vector, launcher_move_dir)
            #         if angle <= 5:
            #             # print("launch br:", np.rad2deg(angle))
            #             if name in cdi.active_players_by_name.keys():
            #                 return cdi.active_players_by_name[name]
            #
            #             if name in cdi.other_units_by_name.keys():
            #                 return cdi.other_units_by_name[name]

        return None
