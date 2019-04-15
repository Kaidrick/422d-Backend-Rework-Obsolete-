import time
import threading

missiles_in_control = {}
recent_missiles = {}
incoming_missiles_by_target_id_name = {}  # assuming target exists


missile_training_range = [  # including A2A training range
    'ECS', 'EC WEST', 'EC EAST',  # Tonopah Electronic Combat Range(TECR) and Electronic Combat Range South Sector
    '4809B', '4807A',  # consists of a few low altitude SAM site
    'R-75W', 'R-75E',  # Live and Dumb Bombing and gunnery training on high value high threat targets such as AAA, SAMs, Industrial complexes, Radar sites, Trains, Convoys and other high value Military targets such as Bridges
]


def log_missile(missile_object):
    missile_data = {
        'data_time': time.time(),
        'missile_data': missile_object
    }
    recent_missiles['id_' + str(missile_object.wpn_object_id)] = missile_data


def clean_obsolete_data():
    for msl_id_name, missile_data_dict in recent_missiles.copy().items():
        data_time = missile_data_dict['data_time']
        if time.time() - data_time > 15:  # data is more than 10 seconds old
            del recent_missiles[msl_id_name]  # remove data from recent missiles log
            print(__file__, "def clean_obsolete_data", f"old data {msl_id_name} removed")


def cleaner():
    while True:
        clean_obsolete_data()
        time.sleep(5)

