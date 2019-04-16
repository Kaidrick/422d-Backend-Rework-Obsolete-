import os
import json
import core.game_object_control.dcs_group_control as dgc
import core.game_object_control.AI as AI
import core.game_object_control.sortie as sortie
import core.game_object_control.command as cmd
import core.game_object_control.mission as miz
from core.game_object_control.dcs_spawn import AddGroup
import core.data_interface as cdi
import threading
import time
import numpy as np
from plugins.declare_plugins import plugin_log
from core.request.miz.dcs_debug import RequestDcsDebugCommand


plugin_name = "Tanker Dispatcher"

tanker_route = [
    'AMOCO', 'AR230V', 'AR231V', 'AR624', 'AR625',
    'AR635', 'AR641A', 'EXPRESS', 'EXXON', 'PEGASUS',
    'PETRO',
]

# load nav pts at start depending on the theatre
# choose from a set of presets for this theatre


def get_route_points(route_name, route_dict):
    kn_route = {}
    for r_n, r_d in route_dict.items():
        if route_name in r_n:
            kn_route[r_n] = r_d
    return kn_route


with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../..', 'data',
                       cdi.theatre) + "/nav_pts.json", 'r+') as f:
    nav_point_dict = json.load(f)
    # print(nav_point_dict)


def Navaid(name):  # return x, y of the navaid of this name
    loc = nav_point_dict[name]
    return {'x': loc['x'], 'y': loc['y']}


dep_arr_gradient = 1000
base_height = 2500  # FIXME: get land height


class TankerPreset:
    rw_to = {
        'Nevada': '3R',
        'PersianGulf': '31R',
        'Caucasus': '12',
    }

    rw_land = {
        'Nevada': '21L',
        'PersianGulf': '13L',
        'Caucasus': '12',
    }

    sid = {
        'Nevada': 'DREAM SIX',
        'PersianGulf': 'Visual',
        'Caucasus': 'Visual',
    }
    star = {
        'Nevada': 'HI-TACAN Y RWY 21L',
        'PersianGulf': 'Visual',
        'Caucasus': 'Visual',
    }
    base_id = {
        'Nevada': 4,
        'PersianGulf': 4,
        'Caucasus': 20,
    }
    base = {
        'Nevada': 'Nellis AFB',
        'PersianGulf': 'Al Dhafra AB',
        'Caucasus': 'Sukhumi-Babushara',
    }


SIDs = {
    'Nevada': {
        'Nellis AFB': {
            'DREAM SIX': {
                '3L': ['ATALF', 'JUNNO 17000'],
                '3R': ['HEREM', 'JUNNO 17000'],
                '21L': ['LAS R-349 7.5', 'MINTT 17000'],
                '21R': ['LAS R-349 7.5', 'MINTT 17000'],
            },
            'FYTTR FIVE': {
                '3L': ['grad 5800', 'LSV R-270 20', 'FYTTR 14000'],
                '3R': ['grad 5800', 'LSV R-270 20', 'FYTTR 14000'],
                '21L': ['LSV R-270 4 5000', 'LSV R-270 10 6000', 'LSV R-270 15 6000', 'FYTTR 14000'],
                '21R': ['LSV R-270 4 5000', 'FYTTR 14000'],
            },
            'MORMON MESA SIX': {
                '3L': ['CUVAX', 'MMM 19000'],
                '3R': ['ZINAX', 'MMM 19000'],
                '21L': ['LAS R-349 7.5', 'RYAAN', 'MMM 19000'],
                '21R': ['LAS R-349 7.5', 'RYAAN', 'MMM 19000'],
            },
        }
    },

    'Caucasus': {
        'Sukhumi-Babushara':  {
            'Visual': {
                '12': ['ALIKA 8000'],
                '30': ['ALIKA 8000'],
            },
        },
    },

    'PersianGulf': {
        'Al Minhad AB':  {
            'Visual': {
                '09': ['UKVAK 10000'],
                '27': ['UKVAK 10000'],
            },
        },
        'Al Dhafra AB': {
            'Visual': {
                '31L': ['SUTVA', 'BOMOS 12000'],
                '31R': ['SUTVA', 'BOMOS 12000'],
                '13L': ['SUTVA', 'BOMOS 12000'],
                '13R': ['SUTVA', 'BOMOS 12000'],
            },
        },
    },
}

STARs = {
    'Nevada': {
        'Nellis AFB': {
            'LOC Z RWY 21L': {
                '21L': ['ARCOE 15000', 'RONKY 15000', 'WISTO 13500',
                        'OLNIE 12500', 'KRYSS 8900', 'SHEET 5000'],
            },
            'LOC X RWY 21L': {
                '21L': ['KRYSS 8900', 'SHEET 5000'],
            },
            'LOC Y RWY 21L': {
                '21L': ['ACOSU 7000', 'BALBE 5900']
            },
            'HI-TACAN RWY 03R': {
                '03R': ['LUCIL 10100', 'HUSTS 6300']
            },
            'HI-TACAN Y RWY 21L': {
                '21L': ['DUDBE 15000', 'SECRT 14000', 'LSV R-283 13 13000',
                        'LSV R-293 13 12000', 'LSV R-303 13 11000',
                        'LSV R-313 13 10000', 'LSV R-323 13 10000',
                        'LSV R-333 13 9500', 'LSV R-343 13 9200',
                        'HOKUM 8800', 'LSV R-013 13 7500',
                        'LSV R-021 13 6000', 'LSV R-021 13 5300'],
            },
        }
    },

    'Caucasus': {
        'Sukhumi-Babushara': {
            'Visual': {
                '12': ['ALIKA'],
                '30': ['ALIKA'],
            },
        },
    },

    'PersianGulf': {
        'Al Minhad AB':  {
            'Visual': {
                '09': ['RARPI'],
                '27': ['RARPI'],
            },
        },
        'Al Dhafra AB': {
            'Visual': {
                '31L': ['MUSEN'],
                '31R': ['MUSEN'],
                '13L': ['MUSEN'],
                '13R': ['MUSEN'],
            },
        },
    },
}


# parse sid points
def load_point(point_string):
    """
    Receive a waypoint in the form of a string
    Split the string by empty space and check each part, then generate a point to be returned
    :param point_string:
    :return:
    """
    # example string key word: grad, R-
    if 'grad' in point_string:  # gradient climb
        print("grad")
    elif 'R-' in point_string:  # radial to a station
        split_point = point_string.split(' ')
        if len(split_point) == 3:  # can it have any other length? maybe altitude as -1
            ref_pt = split_point[0]
            ref_rad = int(float(split_point[1].lstrip('R-')))
            ref_dist = float(split_point[2])

            # print(ref_pt, ref_rad, ref_dist)
            # print(f"Reference Station: {ref_pt} on Radial {ref_rad} at {ref_dist} nautical miles.")

            d_str = {
                'category': 2,  # point defined by nav station radial distance
                'station': ref_pt,
                'radial': ref_rad,
                'distance': float(ref_dist) * 1852,
            }
            return d_str

        elif len(split_point) == 4:  # with alt?
            ref_pt = split_point[0]
            ref_rad = int(float(split_point[1].lstrip('R-')))
            ref_dist = float(split_point[2])
            alt = split_point[3]

            # print(ref_pt, ref_rad, ref_dist, alt)
            # print(f"Reference Station: {ref_pt} on Radial {ref_rad} at {ref_dist} nautical miles, above {alt} feet.")

            d_str = {
                'category': 3,  # point defined by nav station radial distance and with altitude
                'station': ref_pt,
                'radial': ref_rad,
                'distance': float(ref_dist) * 1852,  # this should be converted to meters
                'altitude': alt,
            }
            return d_str

    else:  # a normal 'point' 'altitude' format
        split_point = point_string.split(' ')
        if len(split_point) == 1:  # no given altitude
            nav_point = point_string

            # print(f"Navaids {nav_point}")

            d_str = {
                'category': 0,  # normal way point with no altitude
                'nav_point': nav_point
            }
            return d_str

        elif len(split_point) == 2:  # maybe a given altitude
            nav_point = split_point[0]
            alt = int(split_point[1])
            # print(nav_point, alt)
            # print(f"Navaids {nav_point}, at {alt}")

            d_str = {
                'category': 1,  # normal waypoint with altitude
                'nav_point': nav_point,
                'altitude': alt,
            }
            return d_str


def plan_point(nav_pt_data):
    """
    Take navigation point data and its category.
    Use different method to generate in game point
    :param nav_pt_data:
            depends on its category has different attributes:
            0 - normal waypoint without altitude info
            1 - normal waypoint with altitude info
            2 - radial reference with out altitude info
            3 - radial reference with altitude info
            4 - WIP
    :return: Point object
    """
    cat = nav_pt_data['category']
    if cat == 0 or cat == 1:
        x = Navaid(nav_pt_data['nav_point'])['x']
        y = Navaid(nav_pt_data['nav_point'])['y']
        # nav_pt.alt = 5000  # how to determine the altitude for a point? TODO: set altitude by dist from origin airport

        if cat == 0:
            new_pt = dgc.build_point(x, y, "Fly Over Point", "Turning Point", alt=10000, spd=200)
        else:
            new_pt = dgc.build_point(x, y, "Fly Over Point", "Turning Point", alt=nav_pt_data['altitude'], spd=200)

        return new_pt

    if cat == 2 or 3:
        sta = nav_pt_data['station']
        sta_x = Navaid(sta)['x']
        sta_y = Navaid(sta)['y']
        rad = nav_pt_data['radial']
        dist = nav_pt_data['distance']

        # print("hdg: " + str(rad))
        hdg = rad
        rad = np.deg2rad(rad)

        # print(math.cos(rad), math.sin(rad))

        f_x = sta_x + dist * np.cos(rad)
        f_y = sta_y + dist * np.sin(rad)

        # print("dist is " + str(dist))
        # print(sta_x, sta_y)
        # print(f_x, f_y)

        if cat == 2:
            new_pt = dgc.build_point(f_x, f_y, "Fly Over Point", "Turning Point", alt=10000, spd=200)
        else:  # cat == 3
            new_pt = dgc.build_point(f_x, f_y, "Fly Over Point", "Turning Point", alt=nav_pt_data['altitude'], spd=200)

        return new_pt


def build_departure_route(map, ab, sid, rw):
    """
    use runway and sid to build a departure route list, add origin point
    :param rw: Runway used for departure
    :param sid: SID used for departure
    :return:
    """

    route_points = []

    dep_sid = SIDs[map][ab][sid][rw]

    # origin = nav_point_dict['LSV']
    origin_point = dgc.build_point(0, 0, "Fly Over Point", "Turning Point", alt=0, spd=0)

    route_points.append(origin_point)  # add the origin point to the list

    for pt in dep_sid:
        point_data = load_point(pt)  # get point data
        planned_point = plan_point(point_data)

        route_points.append(planned_point)

    return route_points


def build_arrival_route(map, ab, star, rw):
    """
    use runway and sid to build a departure route list, add origin point
    :param rw: Runway used for departure
    :param star: STAR used for departure
    :return:
    """

    route_points = []

    arr_star = STARs[map][ab][star][rw]

    for pt in arr_star:
        point_data = load_point(pt)  # get point data
        planned_point = plan_point(point_data)

        route_points.append(planned_point)

    return route_points


tanker_flight_plan = {
    'AMOCO': {
        'entry': Navaid('AMOCO.IP'),
        'track': [Navaid('AMOCO.1'), Navaid('AMOCO.2')]
    },
    'PETRO': {
        'entry': Navaid('PETRO.IP'),
        'track': [Navaid('PETRO.1'), Navaid('PETRO.2')]
    },
    'PEGASUS': {
        'entry': Navaid('PEGASUS.IP'),
        'track': [Navaid('PEGASUS.1'), Navaid('PEGASUS.2')]
    },
    'EXXON': {
        'entry': Navaid('EXXON.IP'),
        'track': [Navaid('EXXON.1'), Navaid('EXXON.2')]
    },
    'EXPRESS': {
        'entry': Navaid('EXPRESS.IP'),
        'track': [Navaid('EXPRESS.1'), Navaid('EXPRESS.2')]
    },
}


def group_single_unit_dead(group_name):
    for unit_name, unit_dt in cdi.other_units_by_name.items():  # check if this group name exist in objects
        try:
            unit_group_name = unit_dt.group_name
            if group_name == unit_group_name:
                return False  # group name exists, group is not dead
        except AttributeError:  # this unit does not have a group name
            pass

    plugin_log(plugin_name, f"Group Name: {group_name} is not in db. Group is dead.")
    return True

    # if group_name in db.env_group_dict_by_name.keys():
    #     return False  # group name key exists, group is not dead
    # else:
    #     # group name key does not exist, group is dead
    #     plugin_log(plugin_name, f"Group Name: {group_name} is not in db. Group is dead.")
    #     return True


def find_unit(group_name):
    for unit_name, unit_dt in cdi.other_units_by_name.items():
        try:
            if group_name == unit_dt.group_name:
                return unit_name
        except AttributeError:  # this unit does not have a group name
            pass

    return None


def check_if_no_move():
    return True


def tanker_control(tanker_group_name,
                   ac_type, tanker_track,
                   spd, alt,
                   chn, chn_mode, ident, freq=243000000, callsign=None):

    kn_freq = freq
    kn_callsign = callsign

    # dcs: stage 1 spawn the flight
    plugin_log(plugin_name, f"{tanker_group_name} {ac_type} {tanker_track} - Stage 1")
    # convert spd and alt to metric
    tkr = dgc.Flight(tanker_group_name, sortie.AAR.name).section(1, ac_type, ls_callsign=[callsign])\
        .base(TankerPreset.base_id[cdi.theatre], rdy="cold")
    AddGroup(tkr).send()

    # build departure route
    dep_pts = build_departure_route(cdi.theatre, TankerPreset.base[cdi.theatre],
                                    TankerPreset.sid[cdi.theatre], TankerPreset.rw_to[cdi.theatre])
    plugin_log(plugin_name, f"{tanker_group_name} {ac_type} --> "
                            f"{TankerPreset.base[cdi.theatre]}, {TankerPreset.sid[cdi.theatre]}, "
                            f"{TankerPreset.rw_to[cdi.theatre]}")

    ip = dgc.build_point(tanker_flight_plan[tanker_track]['entry']['x'],
                         tanker_flight_plan[tanker_track]['entry']['y'],
                         "Fly Over Point", "Turning Point", 18000, 400)
    dep_pts.append(ip)

    nm = dgc.Mission(tanker_group_name)
    nm.add_route_point(dep_pts)
    nm.send()

    plugin_log(plugin_name, f"mission sent to {tanker_group_name}")

    time.sleep(5)  # wait for the spawn?

    # dcs: stage 2 check if flight is dead
    plugin_log(plugin_name, f"{tanker_group_name} {ac_type} {tanker_track} - Stage 2")
    tanker_dead = False
    # check if tanker reaches IP
    while True:
        # search group_env_dict_by_name
        if group_single_unit_dead(tanker_group_name):  # group is dead
            tanker_dead = True
            break
        else:  # group is still alive
            unit_name = find_unit(tanker_group_name)
            unit = cdi.other_units_by_name[unit_name]
            pos = unit.unit_pos

            # tkr_group = db.env_group_dict_by_name[tanker_group_name]
            # pos = tkr_group.lead_pos

            dx = abs(ip.x - pos['x'])
            dy = abs(ip.y - pos['z'])
            # print(tanker_group_name, dx, dy)
            if dx < 5000 and dy < 5000:
                plugin_log(plugin_name, f"{tanker_group_name} {ac_type} {tanker_track} - Set Task")
                t1 = dgc.build_point(tanker_flight_plan[tanker_track]['track'][0]['x'],
                                     tanker_flight_plan[tanker_track]['track'][0]['y'],
                                     "Fly Over Point", "Turning Point", alt, spd)
                t2 = dgc.build_point(tanker_flight_plan[tanker_track]['track'][1]['x'],
                                     tanker_flight_plan[tanker_track]['track'][1]['y'],
                                     "Fly Over Point", "Turning Point", alt, spd)

                tk = miz.Tanker(ident, chn, chn_mode, alt, spd).tasks
                t1.add_task(tk)

                m = miz.Mission(tanker_group_name)
                m.add_route_point([t1, t2])

                m.send()

                cmd.SetFrequency(tanker_group_name, frequency=freq).send()
                cmd.ActivateBeacon(tanker_group_name, AI.BeaconType.BEACON_TYPE_TACAN,
                                   AI.BeaconSystem.TACAN_TANKER, ident,
                                   mode_channel=chn_mode, channel=chn, bearing=True).send()

                tanker_data = {
                    'type': ac_type,
                    'on_track_spd': spd,
                    'track': tanker_track,
                    'alt': alt,
                    'chn': chn,
                    'mode': chn_mode,
                    'ident': ident,  # identifier of the beacon
                    'freq': freq,
                    'callsign': callsign
                }
                cdi.tanker_sta[tanker_group_name] = tanker_data

                break

        time.sleep(3)

    # dcs: check fuel
    # FIXME: checking fuel sometimes cause miz env to crash
    # probably because search name is wrong?
    plugin_log(plugin_name, f"{tanker_group_name} {ac_type} {tanker_track} - Stage 3")
    # check if tanker is dead and its fuel?
    while True:
        if tanker_dead:
            break

        # search group_env_dict_by_name
        if group_single_unit_dead(tanker_group_name):
            tanker_dead = True
            # remove tanker from on station list in data interface
            if tanker_group_name in cdi.tanker_sta.keys():
                del cdi.tanker_sta[tanker_group_name]
            break
        else:
            unit_name = find_unit(tanker_group_name)
            unit = cdi.other_units_by_name[unit_name]
            fuel = unit.fuel
            # fuel = RequestDcsDebugCommand(f"return Group.getByName('{tanker_group_name}'):getUnit(1):getFuel()", True).send()  # query miz env

            # any request could fail though
            if fuel:  # if fuel is None
                if fuel < 0.10:
                    plugin_log(plugin_name, f"{tanker_group_name} {ac_type} {tanker_track} - Command RTB")

                    # remove tanker from on station list in data interface
                    if tanker_group_name in cdi.tanker_sta.keys():
                        del cdi.tanker_sta[tanker_group_name]

                    des_gradient = base_height

                    # arr_pts = build_arrival_route('Nevada', 'Nellis AFB', 'HI-TACAN Y RWY 21L', '21L')
                    arr_pts = build_arrival_route(cdi.theatre, TankerPreset.base[cdi.theatre],
                                                  TankerPreset.star[cdi.theatre], TankerPreset.rw_land[cdi.theatre])

                    # arr_pts = []
                    # for pt in arrival:
                    #     pt_p = dgc.build_point(pt['x'], pt['y'],
                    #                            "Fly Over Point", "Turning Point", des_gradient, 150)
                    #     des_gradient -= dep_arr_gradient
                    #     arr_pts.append(pt_p)

                    bm = dgc.Mission(tanker_group_name)
                    bm.add_route_point(arr_pts)
                    bm.send()

                    time.sleep(3)
                    break
                else:
                    # print("fuel level: " + str(fuel))
                    pass
            else:  # fuel is None
                pass

        time.sleep(30)

    # check if tanker shutdown
    last_pos = {}
    plugin_log(plugin_name, f"{tanker_group_name} {ac_type} {tanker_track} - Stage 4")
    while True:
        if tanker_dead:
            break

        if group_single_unit_dead(tanker_group_name):
            tanker_dead = True
            break
        else:
            unit_name = find_unit(tanker_group_name)
            if not unit_name:  # find_unit returns None, cannot find unit, better respawn
                plugin_log(plugin_name, f"{tanker_group_name} {ac_type} {tanker_track} - Cannot find tanker, Remove")
                tanker_dead = True
                break
            unit = cdi.other_units_by_name[unit_name]

            last_pos = unit.unit_pos
            # tkr_group = db.env_group_dict_by_name[tanker_group_name]
            # last_pos = tkr_group.lead_pos
            # print(last_pos)

            time.sleep(60)
            unit_name = find_unit(tanker_group_name)
            if not unit_name:  # find_unit returns None, cannot find unit, better respawn
                plugin_log(plugin_name, f"{tanker_group_name} {ac_type} {tanker_track}"
                                        f" - Cannot find tanker after 60s, Remove")
                tanker_dead = True
                break
            unit = cdi.other_units_by_name[unit_name]  # FIXME: sometimes throws a KeyError
            pos = unit.unit_pos

            # tkr_group = db.env_group_dict_by_name[tanker_group_name]
            #             # pos = tkr_group.lead_pos
            # print(pos)

            if last_pos == pos:
                plugin_log(plugin_name, f"{tanker_group_name} {ac_type} {tanker_track} - Idle for 60s, Remove")
                tanker_dead = True
                break

        time.sleep(60)

    # after break from tanker init point
    if tanker_dead:  # restart the thread after some time?
        plugin_log(plugin_name, f"{tanker_group_name} {ac_type} {tanker_track} - Dead, Respawn in 30s")
        time.sleep(30)
        new_tc = threading.Thread(target=tanker_control,
                                  args=(tanker_group_name, ac_type, tanker_track, spd, alt, chn, chn_mode, ident,
                                        freq, callsign))

        new_tc.start()


def include_dispatch_tankers():
    t1 = threading.Thread(target=tanker_control,
                          args=("KC135MPRS - Track: Petro", "KC135MPRS", 'PETRO', 418, 30000, 7, "X", "PTO"),
                          kwargs={'freq': 244000000, 'callsign': [1, 1, 1, 'Texaco11']})
    t1.start()
    time.sleep(5)
    t2 = threading.Thread(target=tanker_control,
                          args=("KC135 - Track: Petro", "KC-135", 'PETRO', 320, 23000, 17, "X", "TKA"),
                          kwargs={'freq': 245000000, 'callsign': [2, 1, 1, 'Arco11']})
    t2.start()
    time.sleep(5)
    t3 = threading.Thread(target=tanker_control,
                          args=("KC135 - Track: PEGASUS", "KC-135", 'PEGASUS', 350, 23000, 4, "X", "PGS"),
                          kwargs={'freq': 252000000, 'callsign': [3, 1, 1, 'Shell11']})
    t3.start()


def declare():
    pass


if __name__ == '__main__':
    # include_dispatch_tankers()
    # paste = RequestDcsDebugCommand("return coalition.getRefPoints(2)", True).send()
    # print(paste)
    pass

# def test_include_dispatch_tankers_more():
#     t2 = threading.Thread(target=tanker_control("KC135 - Track: Petro",
#                                                 "KC-135", 'PETRO',
#                                                 400, 25000,
#                                                 17, "X", "TKA"))
#
#     t2.start()



    # nav_points_dict = {}
    # ls_navpts = []
    #
    # with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../..', 'data') + "/nttr_navpts.json") as f:
    #     j = json.load(f)
    #     for idx, v in enumerate(j):
    #         nav_points_dict[v['callsignStr']] = {
    #             'x': v['x'], 'y': v['y']
    #         }
    #         # print(v['callsignStr'], v['x'], v['y'])
    #         ls_navpts.append(v['callsignStr'])
    #
    # with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../..', 'data') + "/raw_nav_pts.json", 'r+') as f:
    #     json.dump(nav_points_dict, f)
    #
    # for nav_point, nav_point_data in sorted(nav_points_dict.items()):
    #     print(nav_point, nav_point_data)
