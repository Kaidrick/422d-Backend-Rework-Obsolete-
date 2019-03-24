import numpy as np
import scipy.spatial.distance
import core.data_interface as cdi
import core.request.miz.dcs_env as db
import core.request.miz.dcs_event
import threading
import time
# find group shells? by distance and direction?
# iterate through active weapon dict <-- make sure to get active weapon before pull?
# when event start shooting, find shoot group id
# start a tracker
# tracker iterate through shell dict, find all shells type,
# if shell is not in group shell list, start to track
# otherwise do nothing
# if shell is near aircraft, and is in aircraft's front, add to group shell list
# keep tracking group shell list
# start to track all shells flying in the same direction until event stop shooting
from plugin_functions.range_control.player_tracker import plugin_name

# start to track shells when event start shooting, stop to track on event stop shooting
group_shell_tracker = {}  # contains the organizer thread for each group

group_shell_pair_dict = {}  # contains the shells for a group


# record initiator aircraft's data from shooting start to end
class ShellTracker:
    def __init__(self, group_id):
        self.initiator_group_id = group_id
        self.initiator_pos = []
        self.initiator_vel = []
        self.initiator_data_recording_thread = None
        self.shell_checking_thread = None
        self.shell_checking_fin = False
        self.all_shells = {}
        self.checked_shells = {}
        self.checked_owner_shells = {}
        self.fin_double_checked_shells = {}

    def record_shelling_aircraft_data(self):
        self.initiator_pos.append(db.env_group_dict[self.initiator_group_id].lead_pos)
        self.initiator_vel.append(db.env_group_dict[self.initiator_group_id].lead['velocity'])

    # FIXME: if ever the limitation of players cannot be in the same group is removed
    def check_if_group_shell(self):  # check a shell's position, add checked mark
        print("checking shells")
        kn_group_name = db.env_group_dict[self.initiator_group_id].name
        # print(kn_group_name)
        while not self.shell_checking_fin:
            if self.initiator_group_id in db.env_group_dict.keys():
                for export_id, unit_dt in cdi.unit_precise_positions.items():
                    if 'GroupName' in unit_dt.keys():
                        if unit_dt['GroupName'] == kn_group_name:
                            pos = unit_dt['Position']
                            hdg = unit_dt['Heading']
                            pos_array = np.array([pos['x'], pos['y'], pos['z']])

                            for bal_id, bal_dt in cdi.active_ballistic_objects.items():
                                if bal_id not in self.checked_shells.keys():
                                    self.checked_shells[bal_id] = bal_dt
                                    # if this ballistic object is shell, is in front of this aircraft, and is near to the aircraft
                                    if 'weapons.shells.' in bal_dt["Name"]:
                                        # check if in front of this aircraft, first check aircraft's current position from db
                                        bal_pos = bal_dt['Position']
                                        # check if the direction of shell is about the same as the heading of aircraft?
                                        bal_pos_array = np.array([bal_pos['x'], bal_pos['y'], bal_pos['z']])
                                        shell_dir = bal_pos_array - pos_array
                                        dir_x = shell_dir[0]
                                        dir_y = shell_dir[2]
                                        s_hdg = np.arctan2(dir_y, dir_x)
                                        if s_hdg > 0:
                                            shell_aspect = s_hdg
                                        else:  # hdg <= 0: math.pi + hdg
                                            shell_aspect = np.pi + s_hdg

                                        print("dt", np.rad2deg(np.abs(shell_aspect - hdg)))

                                        dist = scipy.spatial.distance.euclidean(pos_array, bal_pos_array)
                                        print(bal_id, dist)
                                        if dist < 500:
                                            self.checked_owner_shells[bal_id] = bal_dt
                                else:
                                    pass

            time.sleep(0.001)

    def start_checking_shells(self):
        print("called start_checking_shells")
        th = threading.Thread(target=self.check_if_group_shell)
        th.start()

    def stop_checking_shells(self):
        self.shell_checking_fin = True
        print("checked_owner_shells:", len(self.checked_owner_shells.keys()))
        ammo = db.env_group_dict[self.initiator_group_id].lead['ammo']


def find_group_shell(group_id):  # event shooting start calls this method
    # find player group's position, get from db.env_group_dict
    p = db.env_group_dict[group_id]
    p_pos = p.lead_pos
    p_vel = p.lead['velocity']
    p_dir = p.lead['att'][0]  # supposedly where aircraft nose is pointing?

    r_hdg = np.arctan2(p_dir['z'], p_dir['x'])
    if r_hdg > 0:
        hdg = np.rad2deg(r_hdg)
    else:  # hdg <= 0: math.pi + hdg
        hdg = np.rad2deg(np.pi + r_hdg)

    p_pos_array = np.array([p_pos['x'], p_pos['y'], p_pos['z']])
    # for each shell in active list do check its position heading and if its in front of the player aircraft
    for bal_id, bal_dt in cdi.active_ballistic_objects.items():
        s_pos = bal_dt['Position']
        s_hdg = bal_dt['Heading']
        s_pos_array = np.array([s_pos['x'], s_pos['y'], s_pos['z']])
        dist = scipy.spatial.distance.euclidean(p_pos_array, s_pos_array)
        hdg_div = np.abs(np.rad2deg(hdg) - s_hdg)
        print(bal_id, bal_dt['Name'], dist, hdg_div)


def shell_tracker_on_event_shooting_start(event_data):
    group_id = event_data['owner_group_id']
    ammo = db.env_group_dict[group_id].lead['ammo']
    print("what? is this method even called?")
    # print(event_data)

    st = ShellTracker(group_id)
    threading.Thread(target=st.start_checking_shells).start()
    group_shell_tracker[group_id] = st
    print(f"ShellTracker starts for {group_id}, thread: {group_shell_tracker[group_id]}")


def shell_tracker_on_event_shooting_end(event_data):
    group_id = event_data['owner_group_id']
    ammo = db.env_group_dict[group_id].lead['ammo']
    # print(event_data)
    if group_id in group_shell_tracker.keys():
        group_shell_tracker[group_id].stop_checking_shells()


def declare():
    # print("Shell Tracker Declare Event Handler")
    pass
    # core.request.miz.dcs_event.EventHandler.SHOOTING_START[f"{plugin_name}_shell_tracker_shooting_start"] = shell_tracker_on_event_shooting_start
    # core.request.miz.dcs_event.EventHandler.SHOOTING_END[f"{plugin_name}_shell_tracker_shooting_start"] = shell_tracker_on_event_shooting_end
