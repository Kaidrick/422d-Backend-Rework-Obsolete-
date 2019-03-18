# DCS: This is a script that enables an ATIS for each airport in the mission.
# ATIS: broadcast terminal information at a frequency for each airport
from core.game_object_control.dcs_set_command import SetFrequency, TransmitMessage, StopTransmission
from core.request.miz.dcs_weather import RequestDcsWeather, parse_wx
import numpy as np
import time
import os
import json
from random import randint
import core.data_interface as cdi
from plugins.declare_plugins import plugin_log
import core.game_object_control.dcs_spawn as spawn
import core.request.miz.dcs_object as dcs_object


plugin_name = "Airport ATIS"

airport_info = {
    'Nevada': {

        'Tonopah Test Range Airfield': {
            'ATIS': 113000000,
            'ATIS_group': 'ATIS Tonopah Test Range Airfield',
            'ATIS_pos': {'x': -227437, 'z': -174559, 'y': 1689},
            'runways': {
                '32': {  # key: runway number, runway data
                    'pos': {
                        'x': -228169,
                        'z': -173995,
                        'y': 1687,
                    },
                    'hdg': 337,
                    'ils': True,
                },

                '14': {
                    'pos': {
                        'x': -224840,
                        'z': -175403,
                        'y': 1687,
                    },
                    'hdg': 157,
                    'ils': True,
                },
            },
        },


        'Al Dhafra AB': {
            'ATIS': 250700000,
            'ATIS_group': 'ATIS AL DHAFRA AB',
            'ATIS_pos': {'x': -210708, 'z': 172462, 'y': 16},
            'runways': {
                '31R': {  # key: runway number, runway data
                    'pos': {
                        'x': -212141,
                        'z': -171812,
                        'y': 16,
                    },
                    'hdg': 308,
                    'ils': False,
                },

                '31L': {
                    'pos': {
                        'x': -214066,
                        'z': -171499,
                        'y': 16,
                    },
                    'hdg': 308,
                    'ils': False,
                },

                '13L': {
                    'pos': {
                        'x': -209915,
                        'z': -174669,
                        'y': 16,
                    },
                    'hdg': 128,
                    'ils': False,
                },

                '13R': {
                    'pos': {
                        'x': -211842,
                        'z': -174353,
                        'y': 16,
                    },
                    'hdg': 128,
                    'ils': False,
                },
            },
        },

        'North Las Vegas': {
            'ATIS': 118050000,
            'ATIS_group': 'ATIS NORTH LAS VEGAS',
            'ATIS_pos': {'x': -401247, 'z': -31244, 'y': 679},
            'runways': {
                '25': {  # key: runway number, runway data
                    'pos': {
                        'x': -400860,
                        'z': -30991,
                        'y': 679,
                    },
                    'hdg': 267,
                    'ils': False,
                },

                '7': {
                    'pos': {
                        'x': -400924,
                        'z': -32489,
                        'y': 679,
                    },
                    'hdg': 87,
                    'ils': False,
                },

                '12R': {
                    'pos': {
                        'x': -400781,
                        'z': -32429,
                        'y': 679,
                    },
                    'hdg': 133,
                    'ils': False,
                },

                '12L': {
                    'pos': {
                        'x': -401079,
                        'z': -31806,
                        'y': 679,
                    },
                    'hdg': 133,
                    'ils': False,
                },

                '30L': {
                    'pos': {
                        'x': -401778,
                        'z': -31372,
                        'y': 679,
                    },
                    'hdg': 313,
                    'ils': False,
                },

                '30R': {
                    'pos': {
                        'x': -401825,
                        'z': -31010,
                        'y': 679,
                    },
                    'hdg': 313,
                    'ils': False,
                },
            },
        },
    },
}

Airdromes = {}


def load_data():
    search_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data', cdi.theatre)

    for filename in os.listdir(search_path):
        if filename.endswith('.json'):
            with open(os.path.join(search_path, filename)) as f:
                ab_dict = json.load(f)
                Airdromes[filename[:-5]] = ab_dict


alphabetic = [
    'Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot', 'Golf',
    'Hotel', 'India', 'Juliet', 'Kilo', 'Lima', 'Mike', 'November',
    'Oscar', 'Papa', 'Quebec', 'Romeo', 'Sierra', 'Tango',
    'Uniform', 'Victor', 'Whiskey', 'Xray', 'Yankee', 'Zulu'
]

ATIS = {}  # generated ATIS message
ATIS_update_time = 0
ATIS_dt = 600  # in second
ATIS_broadcast_duration = 15
ATIS_msg_wait = 5


def generate_atis_message():
    global ATIS_update_time
    if time.time() - ATIS_update_time >= ATIS_dt:
        # msg = f"last update time is {ATIS_update_time}, now is {time.time()}, dt is {time.time() - ATIS_update_time} second. Genrate new ATIS!"
        msg = f"New ATIS Info Generated on T = Epoch {time.time():.0f}"
        plugin_log(plugin_name, msg)
        ATIS_update_time = time.time()
        airbases = Airdromes

        for ab, ab_data in airbases.items():
            # get runways
            pos_ls = []
            for rw_name, rw_data in ab_data['runways'].items():
                pos = rw_data['pos']
                pos_ls.append(pos)

            # print(pos_ls)
            f_data = RequestDcsWeather(pos_ls).send()
            # print(ab_data['runways'].keys())

            diffs = {}

            for idx, wx_data in enumerate(f_data):
                rw_num = list(ab_data['runways'].keys())[idx]
                wind_dir = parse_wx(wx_data)['wind_dir']
                rw_hdg = list(ab_data['runways'].values())[idx]['hdg']
                abs_angle_diff = np.abs(wind_dir - rw_hdg)
                diffs[rw_num] = abs_angle_diff

            # print(diffs.keys(), diffs.values())
            x = np.array(list(diffs.values()))
            # print(x)
            # print(np.argmin(x))
            use_rw = list(diffs.keys())[np.argmin(x)]
            met_cond_dict = parse_wx(f_data[np.argmin(x)])
            # print(met_cond_dict)
            mag_wind_dir = met_cond_dict['mag_wind_dir']
            wind = met_cond_dict['wind']
            wind_kt = met_cond_dict['wind_kt']
            oat = met_cond_dict['oat_celsius']
            qnh_hp = met_cond_dict['qnh_hp']
            qnh_inhg = met_cond_dict['qnh_inhg']

            k = randint(0, len(alphabetic) - 1)
            info_letter = alphabetic[k]

            gmt = time.gmtime()
            timeString = time.strftime("%H%M", gmt)

            if wind_kt <= 1:  # wind calm
                msg = "Automatic Terminal Information Service " + f"({ab}): " + "\n" + \
                    f'{ab} ATIS Information {info_letter} {timeString} ZULU' + "\n" + \
                    "Wind " + "Calm" + "\n" + \
                    f"Temperature {oat:.0f} " + "\n" + \
                    f"Altimeter {qnh_inhg:.2f} (or {qnh_hp:.0f}hP)" + "\n" + \
                    f"Landing and departing runway is {use_rw}" + "\n" + \
                    f"Helicopter control open on tower frequency" + "\n" + \
                    f"On initial contact inform tower you have information {info_letter}"
            else:
                msg = "Automatic Terminal Information Service " + f"({ab}): " + "\n" + \
                    f'{ab} ATIS Information {info_letter} {timeString} ZULU' + "\n" + \
                    "Wind " + f"{mag_wind_dir:05.1f} at {wind_kt:.0f} (or {wind:.0f} meters per second)" + "\n" + \
                    f"Temperature {oat:.0f} " + "\n" + \
                    f"Altimeter {qnh_inhg:.2f} (or {qnh_hp:.0f}hP)" + "\n" + \
                    f"Landing and departing runway is {use_rw}" + "\n" + \
                    f"Helicopter control open on tower frequency" + "\n" + \
                    f"On initial contact inform tower you have information {info_letter}"

            ATIS[ab] = (ab_data['ATIS_group'], ab_data['ATIS'], msg)

            cdi.d_atis[ab] = {
                'info_ident': info_letter,
                'time_string': timeString,
                'mag_wind_dir': mag_wind_dir,
                'wind_kt': wind_kt,
                'wind_mps': wind,
                'oat': oat,
                'altimeter': qnh_inhg,
                'altimeter_hp': qnh_hp,
                'rw_in_use': use_rw,
            }

    else:
        # print("no need to generate new ATIS")
        pass


def broadcast_atis_message():
    for ab, send_dt in ATIS.items():
        StopTransmission(send_dt[0]).send()
        SetFrequency(send_dt[0], power=10, frequency=send_dt[1]).send()
        TransmitMessage(send_dt[0], send_dt[2], ATIS_broadcast_duration, loop=False, file="Static_Short").send()


def spawn_atis_stations():
    load_data()
    airbases = Airdromes

    for ab, ab_data in airbases.items():
        # get name of atis group
        # get position of atis group
        group_name = ab_data['ATIS_group']
        pos = ab_data['ATIS_pos']
        print(ab_data['ATIS_group'], ab_data['ATIS_pos'])

        atis = dcs_object.Unit(group_name, pos['x'], pos['z'])
        atis.type = "Soldier M249"  # "2B11 mortar"
        atis.skill = "Excellent"

        atis_group = dcs_object.Group(group_name, pos['x'], pos['z'])
        atis_group.add_unit(atis)
        atis_group.task = "Ground Nothing"
        atis_group.hidden = True

        spawn.AddGroup(atis_group.__dict__, 2, dcs_object.Category.GROUND_UNIT).send()


def write_data_as_airport_json_file():
    import json
    this_nellis = airport_info['Nevada']['Creech AFB']
    filename = "data/Nevada/Creech AFB.json"
    with open(filename, 'r+') as f:
        f.seek(0)
        json.dump(this_nellis, f)
        f.truncate()


def atis_timer():
    spawn_atis_stations()
    while True:
        generate_atis_message()
        broadcast_atis_message()
        time.sleep(ATIS_broadcast_duration + ATIS_msg_wait)


def include_airport_atis():
    import threading

    atis_con = threading.Thread(target=atis_timer)
    atis_con.start()





if __name__ == '__main__':
    import json

    this_nellis = airport_info['Nevada']['Al Dhafra AB']
    filename = "data/PersianGulf/Al Dhafra AB.json"
    with open(filename, 'r+') as f:
        f.seek(0)
        json.dump(this_nellis, f)
        f.truncate()
