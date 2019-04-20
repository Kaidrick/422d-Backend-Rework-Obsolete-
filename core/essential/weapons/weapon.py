"""
This file implements data model for general purpose bomb and guided bomb
what about sub-munition you ask?
"""
import core.data_interface as cdi
import collections
import numpy as np
import core.spark as spark
import core.utility.data_parsing as parse


class Weapon:
    def __init__(self, weapon_runtime_id, weapon_data, timestamp):
        # what kind of data does this model needs?
        # position
        # speed?
        self.runtime_id = int(weapon_runtime_id[3:])  # numerical
        self.wpn_id_name = weapon_runtime_id  # string
        self.export_name = weapon_data['Name']  # name of the type? maybe? need further testing
        self.display_name = parse_munition_type_name(self.export_name)  # weapon type in general
        self.ws_type = weapon_data['Type']  # level 1 to level 4
        self.category = self.ws_type['level2']  # 4, 5, 6, 7 --> MSL BOMB SHELL NURS

        # initial launch position
        self.init_pos = weapon_data['Position']
        self.init_ll = weapon_data['LatLongAlt']
        self.init_heading = weapon_data['Heading']
        self.init_pitch = weapon_data['Pitch']
        self.init_bank = weapon_data['Bank']

        # launcher info
        self.launcher = self.find_launcher()  # model object of a player or an other_unit

        # model data
        self.launch_time = timestamp

        if self.launcher:
            self.init_velocity = self.launcher.velocity  # this should be the aircraft speed?

            int_vel = np.array([
                self.init_velocity['x'], self.init_velocity['y'], self.init_velocity['z']
            ])
            self.init_spd = np.linalg.norm(int_vel)
        else:
            self.init_spd = 0

        self.end_time = 0
        self.flight_time = 0
        self.terminal_speed_average = 0

        self.velocity = []  # this should be a list or vector or something?
        self.speed = 0  # a number, calculated by distance delta over time delta

        self.trajectory = collections.deque(maxlen=5)  # contains trajectory position of the object
        self.attitude = collections.deque(maxlen=5)
        self.geo_coord = collections.deque(maxlen=5)

        self.timestamp = collections.deque(maxlen=5)

        self.terminal_speed = collections.deque(maxlen=20)

        # append data
        self.trajectory.append(self.init_pos)
        self.geo_coord.append(self.init_ll)
        self.timestamp.append(timestamp)

        # if self.launcher:  # not None
        #     print(f"LAUNCH: {self.launcher.runtime_id_name}({self.launcher.unit_type})")
        #     pass
        # else:
        #     print("No launcher is found for some reason")
        if not self.launcher:
            print("No launcher is identified?")

    def update(self, unit_data, timestamp):  # position and attitude

        # also tries to find launcher runtime id from triggered events if launcher is not found in previous iter

        # check if sequence has equal value pairs?
        if self.trajectory[-1] == unit_data['Position']:
            print("bad export data of same simulation frame!")
        else:  # if not bad data, calculate distance difference
            last_pos_array = np.array([self.trajectory[-1]['x'], self.trajectory[-1]['y'], self.trajectory[-1]['z']])
            new_pos_array = np.array([unit_data['Position']['x'],
                                      unit_data['Position']['y'],
                                      unit_data['Position']['z']])
            dist = np.linalg.norm(new_pos_array - last_pos_array)
            d_time = timestamp - self.timestamp[-1]
            self.terminal_speed.append(dist/d_time)  # meters per second

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

        # print("check ", t_check_pos)

        # maybe combine this two dicts?
        # search dict contains only player or other unit model object, not raw export data
        # TODO: so only player or other unit can be launcher, what about cluster bomb and WCMD?
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
                launcher_move_dir = launcher_object.move_dir  # array
                t_launcher_pos = np.array([launcher_pos['x'], launcher_pos['z']])
                launcher_alt = launcher_pos['y']
                # check 3d distance between this player's pos and this current weapons position
                dist = np.linalg.norm(t_check_pos - t_launcher_pos)  # distance between weapon launch position and this A/C
                # print("wpn check dist: ", dist, "wpn check height: ", launcher_alt - check_alt)

                # TODO: the position of this weapon should be in front of the launcher aircraft
                # TODO: that is to say, the angle between a/c move direction array and
                # TODO: the vector from player aircraft to the weapon should be within certain limit
                # TODO: in nose quarter is tolerable?

                if dist < 100:  # TODO: this value need more tweaking for rockets?
                    # if within feasible range limit, check direction
                    array_wpn_init_pos = np.array([
                        self.init_pos['x'], self.init_pos['y'], self.init_pos['z']
                    ])
                    array_launcher_pos = np.array([
                        launcher_pos['x'], launcher_pos['y'], launcher_pos['z']
                    ])
                    array_wpn_launch_vector = array_wpn_init_pos - array_launcher_pos
                    # check angle to move_dir
                    angle = parse.angle_between(array_wpn_launch_vector, launcher_move_dir)
                    if angle <= 90:
                        # print("launch br:", np.rad2deg(angle))

                        # need to return address of the launcher object in cdi
                        if name in cdi.active_players_by_name.keys():
                            return cdi.active_players_by_name[name]

                        if name in cdi.other_units_by_name.keys():
                            return cdi.other_units_by_name[name]

                else:
                    # print(f"mismatched distance for type {self.display_name}, dist: {dist}")
                    pass
                    # if within feasible range limit, check direction

        #
        # # check if player launched this weapon
        # for name, player_object in cdi.active_players_by_name.items():
        #     player_runtime_id_name = player_object.runtime_id_name
        #     try:
        #         player_dt = cdi.export_omni[player_runtime_id_name]
        #     except KeyError as e:  # cannot find this id in export data, either data is wrong, or player is inactive
        #         print(e)
        #     else:
        #         player_pos = player_dt['Position']
        #         t_player_pos = np.array([player_pos['x'], player_pos['z']])
        #         player_alt = player_pos['y']
        #         # check 3d distance between this player's pos and this current weapons position
        #         dist = np.linalg.norm(t_check_pos - t_player_pos)  # distance between weapon launch position and this A/C
        #         print("wpn check dist: ", dist, "wpn check height: ", player_alt - check_alt)
        #         if dist < 5:
        #             return player_object
        #
        # # check if AI launched this weapon
        # for other_name, other_object in cdi.other_units_by_name.items():
        #     other_runtime_id_name = other_object.runtime_id_name

        # search is done and no launcher can be found for some reason
        return None

    def final(self):
        """
        Finalize data for this weapon. Used when weapon terminal spark is triggered
        :return:
        """
        # push to player weapon release record? so when player is dead the record is also erased
        # find player
        try:  # only find player, if AI launched this weapon then ignore? at least for the moment
            kn_active_player = cdi.active_players_by_name[self.launcher.player_name]
        except KeyError:
            print(f"player {self.launcher.player_name} is no longer active, ignore")
            pass
        except AttributeError:
            print("not launched by a player, ignore")
            pass
        else:  # push data to player record

            # there could be a ZeroDivisionError: division by zero

            # finalize self data
            try:
                self.terminal_speed_average = sum(self.terminal_speed) / len(self.terminal_speed)
            except ZeroDivisionError:
                print("bad data because of ZeroDivision")
            else:
                self.flight_time = self.timestamp[-1] - self.launch_time

            kn_active_player.player_stat.weapons_released.append(self)
            # print(f"weapon release record added to player stats of \"{kn_active_player.player_name}\"")


def finalize_weapon_record(spk_dt):
    wpn_object = spk_dt['data']['self']
    wpn_object.final()


spark.SparkHandler.WEAPON_TERMINAL["weapon_record_fin"] = finalize_weapon_record


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
