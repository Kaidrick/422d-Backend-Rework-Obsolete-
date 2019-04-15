"""
This file implements data model for general purpose bomb and guided bomb
what about sub-munition you ask?
"""
import collections
import core.data_interface as cdi
import numpy as np
from .weapon import Weapon


class Bomb(Weapon):
    def __init__(self, weapon_runtime_id, weapon_data, timestamp):
        super().__init__(weapon_runtime_id, weapon_data, timestamp)

    # what differs bomb from other types of ammunition?
    # launch criteria --> check distance is different
    #                 --> check direction for bullet stream?
    # bomb can be rippled or paired

    # rewrite find_launcher here because criteria is different
    def find_launcher(self):
        t_check_pos = np.array([self.init_pos['x'], self.init_pos['z']])
        check_alt = self.init_pos['y']

        search_dict = {**cdi.active_players_by_name, **cdi.other_units_by_name}

        # check find the player or the other_unit who launched this weapon
        for name, launcher_object in search_dict.items():
            runtime_id_name = launcher_object.runtime_id_name
            try:
                launcher_dt = cdi.export_omni[runtime_id_name]
            except KeyError as e:  # cannot find this id in export data, either data is wrong, or player is inactive
                print(e)
            else:
                launcher_pos = launcher_dt['Position']
                t_launcher_pos = np.array([launcher_pos['x'], launcher_pos['z']])
                launcher_alt = launcher_pos['y']
                # check 3d distance between this player's pos and this current weapons position
                dist = np.linalg.norm(
                    t_check_pos - t_launcher_pos)  # distance between weapon launch position and this A/C
                # print("wpn check dist: ", dist, "wpn check height: ", launcher_alt - check_alt)
                if dist < 3:  # distance less than 3 meters for bombs
                    # need to return address of the launcher object in cdi
                    if name in cdi.active_players_by_name.keys():
                        return cdi.active_players_by_name[name]

                    if name in cdi.other_units_by_name.keys():
                        return cdi.other_units_by_name[name]

        return None
