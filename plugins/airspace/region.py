"""This is a file that contains the definition of an airspace as well as methods related to airspace"""
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import scipy.spatial.distance
import numpy as np
import core.data_interface as cdi
import os
import configparser
import threading
import time
import core.spark as spark

theatre = cdi.theatre


class Airspace:
    def __init__(self, as_def):
        """
        Take the name and definition of an airspace. Airspace definition should be a dict
        :param name:
        :param as_def:
        """
        self.name = as_def['Name'].title()
        if as_def['Upper Limit'] == "UNL":  # unlimited level
            self.upper_limit = 30000  # set to 30000 meters
        else:
            if 'FL' in as_def['Upper Limit']:  # is FL xxx
                self.upper_limit = float(as_def['Upper Limit'].lstrip('FL')) * 100 / 3.281  # convert to meters
            else:  # in feet
                self.upper_limit = float(as_def['Upper Limit'].split(' ')[0]) / 3.281

        if as_def['Lower Limit'] == "GND":
            self.lower_limit = 0
        else:
            if 'FL' in as_def['Lower Limit']:
                self.lower_limit = float(as_def['Lower Limit'].lstrip('FL')) * 100 / 3.281
            else:
                self.lower_limit = int(as_def['Lower Limit'].split(' ')[0]) / 3.281

        self.designator = as_def['Designator']
        # self.raw_regions = as_def['Region']
        self.regions = []
        self.type = as_def['Type']
        self.parse(as_def['Region'])

    def parse(self, regions):  # check if given vec3 pos is in this airspace
        for region in regions.split('\n'):  # check what type each region is then check if given pos is in region
            # print(self.name, region)
            # convert region string
            # check what kind of region def this is:
            r_dt = region.split(' ')
            if len(r_dt) == 5:  # circular definition
                # print(self.name, "Rectangle Region", [float(d_dt) for d_dt in r_dt])
                self.regions.append({'type': 0, 'def': [float(d_dt) for d_dt in r_dt]})
            else:  # rectangle definition
                p_num = int(len(r_dt) / 2)  # total number of points
                pts = []
                # get pairs
                for pair_num in range(0, p_num):  # get 0,1 in 0, get 2,3 in 1, get 4,5 in 2, get 6,7 in 3
                    x_i = 2 * pair_num
                    y_i = 2 * pair_num + 1
                    _pt = (float(r_dt[x_i]), float(r_dt[y_i]))
                    pts.append(_pt)
                    # print(f"Point {pair_num}: {_pt}")
                # print(self.name, "Rectangle Region", pts)
                self.regions.append({'type': 1, 'def': pts})

    def region_show(self):
        print(self.name, self.regions)

    def check(self, pos):  # pos is a vec3 {'x': 0, 'y': 0, 'z': 0}
        for region in self.regions:
            # check alt first
            if pos['y'] < self.upper_limit:
                if pos['y'] > self.lower_limit:  # is in altitude within this airspace
                    if region['type'] == 0:  # circular definition: check dist to origin, check aspect angle, check alt
                        pos_array = np.array([pos['x'], pos['z']])
                        x = region['def'][0]
                        y = region['def'][1]
                        aspect_angle_0 = region['def'][2]
                        aspect_angle_1 = region['def'][3]
                        radius = region['def'][4] * 1000

                        dx = pos['x'] - x
                        dy = pos['z'] - y
                        pc_asp_agl = np.arctan2(dy, dx)
                        if pc_asp_agl >= 0:
                            p_asp_agl = pc_asp_agl
                        else:
                            p_asp_agl = pc_asp_agl + np.pi * 2

                        coc_array = np.array([x, y])
                        dist = scipy.spatial.distance.euclidean(coc_array, pos_array)

                        # print(f"Aspect angle is {np.rad2deg(p_asp_agl)}")
                        # print(f"Dist to origin is {dist}, and radius is {radius}")

                        if dist < radius:
                            if np.rad2deg(p_asp_agl) > aspect_angle_0:
                                if np.rad2deg(p_asp_agl) < aspect_angle_1:  # check if aspect angle is in range
                                    return True

                    elif region['type'] == 1:  # poly definition: check if point in region
                        poly = Polygon(region['def'])
                        pt = Point(pos['x'], pos['z'])
                        if poly.contains(pt):
                            return True

        # if all region is checked and does not return
        return False  # this pos is not in this airspace


airspace = []


def load_airspace():  # load data from config files according to initial theatre
    config_data_file = theatre + '.cfg'
    file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', config_data_file)
    cfg = configparser.ConfigParser()
    cfg.read(file_path)

    print(str(len(cfg.sections())) + " section(s) of airspace for " + theatre + " loaded")

    for section in cfg.sections():
        new_air_space = Airspace(cfg[section])
        airspace.append(new_air_space)


def locate_airspace(pos):
    for asp in airspace:
        if asp.check(pos):  # pos is in this airspace
            return asp.designator


def airspace_tracker():
    load_airspace()

    while True:
        for player_name, player_dt in cdi.active_players_by_name.items():
            player_pos = player_dt.unit_pos

            last_airspace = player_dt.get_airspace()
            player_airspace = locate_airspace(player_pos)
            player_dt.set_airspace(player_airspace)

            if not last_airspace == player_airspace:  # airspace change
                # airspace change spark here
                spk_dt = {
                    'type': 'airspace_change',
                    'data': {
                        'player_name': player_name,
                        'runtime_id': player_dt.runtime_id_name,
                        'last_airspace': last_airspace,
                        'current_airspace': player_airspace,
                    }
                }
                spark.player_airspace_change(spk_dt)

                print(f"{player_dt.player_name} ({player_dt.unit_type}, ID: {player_dt.runtime_id}) - Airspace Change: "
                      f"{last_airspace} > {player_airspace}")

            # print(player_pos, player_airspace)
            # print(player.get_airspace())

        time.sleep(1)


def declare():
    threading.Thread(target=airspace_tracker).start()


if __name__ == '__main__':
    from core.request.miz.dcs_debug import RequestDcsDebugCommand
    load_airspace()
#
    print(locate_airspace({'x': -233947, 'y': 1551, 'z': -195750}))
