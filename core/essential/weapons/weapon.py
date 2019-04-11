"""
This file implements data model for general purpose bomb and guided bomb
what about sub-munition you ask?
"""
import core.data_interface as cdi
import collections
import numpy as np


class Weapon:
    def __init__(self, weapon_runtime_id, weapon_data, timestamp):
        # what kind of data does this model needs?
        # position
        # speed?
        self.runtime_id = int(weapon_runtime_id[3:])  # numerical
        self.wpn_id_name = weapon_runtime_id  # string
        self.export_name = weapon_data['Name']  # name of the type? maybe? need further testing
        self.display_name = parse_munition_type_name(self.export_name)
        self.ws_type = weapon_data['Type']  # level 1 to level 4

        # initial launch position
        self.init_pos = weapon_data['Position']
        self.init_ll = weapon_data['LatLongAlt']
        self.init_heading = weapon_data['Heading']
        self.init_pitch = weapon_data['Pitch']
        self.init_bank = weapon_data['Bank']

        # launcher info
        # self.launcher_runtime_id = self.find_launcher()
        self.launcher_runtime_id = None
        self.launcher_group_id = None

        # model data
        self.launch_time = timestamp
        self.end_time = 0
        self.flight_time = 0

        self.velocity = []  # this should be a list or vector or something?
        self.speed = 0  # a number, calculated by distance delta over time delta

        self.trajectory = collections.deque(maxlen=5)  # contains trajectory position of the object
        self.attitude = collections.deque(maxlen=5)
        self.geo_coord = collections.deque(maxlen=5)

        self.timestamp = collections.deque(maxlen=5)

        # append data
        self.trajectory.append(self.init_pos)
        self.geo_coord.append(self.init_ll)
        self.timestamp.append(timestamp)

    def update(self, unit_data, timestamp):  # position and attitude

        # also tries to find launcher runtime id from triggered events if launcher is not found in previous iter

        self.trajectory.append(unit_data['Position'])
        self.geo_coord.append(unit_data['LatLongAlt'])

        self.timestamp.append(timestamp)

        return self

    def is_active(self):
        """
        Check if this weapon is still active: pos and att changing
        :return:
        """
        if all(trj == self.trajectory[0] for trj in self.trajectory) and \
           all(att == self.attitude[0] for att in self.attitude) and \
           len(self.trajectory) == 5 and len(self.attitude) == 5:
            return False
        else:
            return True

    def find_launcher(self):  # not very reliable it seems to be
        # search in cdi for nearest unit?
        # is it necessary to check AI?
        # for consistency, maybe, but always check player first
        t_check_pos = np.array([self.init_pos['x'], self.init_pos['z']])
        check_alt = self.init_pos['y']

        print("check ", t_check_pos)
        # check if player launched this weapon
        for name, player_dt in cdi.active_players_by_name.items():
            player_runtime_id_name = 'id_' + str(player_dt.runtime_id)
            try:
                player_dt = cdi.export_omni[player_runtime_id_name]
            except KeyError as e:  # cannot find this id in export data, either data is wrong, or player is inactive
                print(e)
            else:
                player_pos = player_dt['Position']
                t_player_pos = np.array([player_pos['x'], player_pos['z']])
                player_alt = player_pos['y']
                # check 3d distance between this player's pos and this current weapons position
                dist = np.linalg.norm(t_check_pos - t_player_pos)  # distance between weapon launch position and this A/C
                print(dist, player_alt - check_alt)
                if dist < 30:
                    return player_runtime_id_name

        # check if AI launched this weapon

        return None

    def final(self):
        """
        Finalize data for this weapon. Used when weapon terminal spark is triggered
        :return:
        """
        self.launcher_runtime_id = 'id_' + str(cdi.weapon_shot_event_log[self.runtime_id]['launcher_object']['id_'])

        del cdi.weapon_shot_event_log[self.runtime_id]


def parse_munition_type_name(export_name):
    # something like weapons.nurs.Zuni_127
    if '.' in export_name:
        t_name = export_name.split('.')
        pt_name = t_name[-1].replace('_', '-').upper()
        return pt_name
    else:
        print("non formatted type display name: ", export_name)
        return export_name


if __name__ == '__main__':

    gap = "weapons.bombs.Mk_82"
    print(parse_munition_type_name(gap))
