"""
track active weapon
in-game shot event start the tracker
in-game hit? or weapon not active?
"""
from core.request.miz.dcs_debug import RequestDcsDebugCommand
from plugins.range_control.obsolete.weapon_delivery_evaluation import weapon_release_data
import threading
import time
import numpy as np
import core.data_interface as cdi
import core.request.miz.dcs_event
from plugins.range_control.obsolete.player_tracker import plugin_name

# k = RequestDcsEvent().send()
# print(k)


class WeaponTracker:  # event shot init a weapon tracker object
    def __init__(self, wpn_dt):
        self.lua_object = wpn_dt['object']
        self.lua_object_id = wpn_dt['object']['id_']
        self.unit_id_name = 'id_' + str(self.lua_object_id)

        self.launcher_object = wpn_dt['launcher_object']
        self.launcher_group_id = wpn_dt['launcher_group_id']
        self.launcher_vector_data = wpn_dt['launcher_vector_data']  # contains p, x, y and z
        self.launcher_init_vel_data = wpn_dt['launcher_vel_data']
        self.launcher_init_ll_coord = wpn_dt['launcher_init_ll_coord']
        self.launcher_init_mgrs_coord = wpn_dt['launcher_init_mgrs_coord']

        self.launch_time = wpn_dt['launch_time']  # FIXME: use os.time() rather than dcs model time
        self.weapon_type = wpn_dt['type']
        self.weapon_vector_data = wpn_dt['vector_data']
        self.weapon_vel_data = wpn_dt['vel_data']

        self.weapon_category = wpn_dt['desc']['category']

        self.cycle = False

        self.wpn_dt = wpn_dt

        self.time_last_update = 0
        self.flight_time = 0
        self.impact_point = []
        self.impact_ll_coord = []
        self.impact_mgrs_coord = []
        self.query_ip_vec3 = None
        self.query_ip_ll = None

        self.trajectory_precise_pos = []
        self.trajectory_precise_ll_coord = []
        self.trajectory_precise_ref_time = []

        self.trajectory_pos = []
        self.trajectory_ll_coord = []
        self.trajectory_mgrs_coord = []
        self.trajectory_att = []
        self.trajectory_velocity = []

        # for display:
        self.dis_init_spd = 0  # meters per second
        self.dis_init_hdg = 0
        self.dis_init_alt = 0
        self.dis_term_spd = 0
        self.dis_term_angle = 0
        self.dis_fl_dist = 0  # for missiles only
        self.dis_ip_coord = ""
        self.dis_ip_tgt_dist = 0
        self.dis_tof = 0  # time of flight

    def fin(self):  # finalize weapon tracker object
        # initial position, direction and speed, which is the launch aircraft vectors --> get from event shot
        launch_dir = self.weapon_vector_data['x']  # vec3
        launch_pos = self.launcher_vector_data['p']  # vec3
        launch_vel = self.launcher_init_vel_data

        # launch speed
        spd_array = np.array([launch_vel['x'], launch_vel['y'], launch_vel['z']])
        self.dis_init_spd = np.linalg.norm(spd_array)
        # launch direction / heading
        dir_x = launch_dir['x']
        dir_y = launch_dir['z']
        hdg = np.arctan2(dir_y, dir_x)
        if hdg > 0:
            self.dis_init_hdg = np.rad2deg(hdg)
        else:  # hdg <= 0: math.pi + hdg
            self.dis_init_hdg = np.rad2deg(np.pi + hdg)

        # launch position --> need LL or MGRS coord
        # launch attitude (dive / roll / yaw)
        # launch altitude
        self.dis_init_alt = launch_pos['y']  # in meters
        # terminal speed                                    --> estimate from last update
        # term_vel = self.trajectory_velocity[-1]
        # term_spd_array = np.array([term_vel['x'], term_vel['y'], term_vel['z']])

        # use s = v * t
        # find s
        p1 = self.trajectory_precise_pos[-1]  # get last pos
        p0 = self.trajectory_precise_pos[-2]  # get second last pos

        g_idx = -2
        while True:
            if p0 == p1:  # if last pos is equal to second last pos
                g_idx -= 1
                p0 = self.trajectory_precise_pos[g_idx]
            else:  # find until equal
                break  # break loop if find first unequal

        # if p0 == p1:
        #     p0 = self.trajectory_precise_pos[-3]  # FIXME: why is the data not updated? export output limit?

        # distance in 3d space for
        ds_array = np.array([p1['x'], p1['y'], p1['z']]) - np.array([p0['x'], p0['y'], p0['z']])
        ds = np.linalg.norm(ds_array)  # distance

        norm_ds = ds_array / ds

        # query lua for impact point
        cmd = f"""
            ip_vec3 = land.getIP(
                {{x = {p1['x']}, y = {p1['y']}, z = {p1['z']}}},  -- last position
                {{x = {norm_ds[0]}, y = {norm_ds[1]}, z = {norm_ds[2]}}},  -- normalized vector
                250
            )
            if ip_vec3 then  -- return L/L as well
                trigger.action.smoke(ip_vec3, 1)
                local latitude, longitude, altitude = coord.LOtoLL(ip_vec3)
                local ip_ll = {{["Lat"] = latitude, ["Long"] = longitude, ["Alt"] = altitude}}
                return {{ip_vec3, ip_ll}}
            else
                return nil
            end
        """

        res_ip = RequestDcsDebugCommand(cmd, True).send()  # if None, use last position?
        if res_ip:
            self.query_ip_vec3 = res_ip[0]  # vec3 dict
        else:
            self.query_ip_vec3 = self.trajectory_precise_pos[-1]

        # find t
        t1 = self.trajectory_precise_ref_time[-1]
        t0 = self.trajectory_precise_ref_time[g_idx]  # first not equal to -1 time
        dt = t1 - t0
        print(ds, dt)
        if dt != 0:
            self.dis_term_spd = ds / dt
        else:
            self.dis_term_spd = 0

        # self.dis_term_spd = np.linalg.norm(term_spd_array)
        # terminal angle                                    --> estimate from last update
        # actual flight distance (for missiles only)        --> estimate from all updates
        # impact point coord                                --> estimate from last update with getIP

        if res_ip:
            # ip_point_ll = self.trajectory_precise_ll_coord[-1]  # should query ll as well?
            ip_point_ll = res_ip[1]
        else:
            ip_point_ll = self.trajectory_precise_ll_coord[-1]  # should query ll as well?

        self.dis_ip_coord = f"{ip_point_ll['Lat']}\t{ip_point_ll['Long']}"
        # impact point to target distance                   --> estimate and calculate

        # time of flight                                    --> estimate
        self.dis_tof = self.trajectory_precise_ref_time[-1] - self.trajectory_precise_ref_time[0]

        # set final tracker
        self.cycle = True

    def update_precise_pos(self):
        updated_once = False
        q_str = "id_" + str(self.lua_object_id)

        # print(self.weapon_type)  # if weapon is a missile, check precision position in unit table
        while True:
            if q_str in cdi.active_ballistic_objects.keys():
                precise_dt = cdi.active_ballistic_objects[q_str]
                # data that cannot be obtained through precise_dt: impact point, velocity
                wpn_pos = precise_dt['Position']
                wpn_ll = precise_dt['LatLongAlt']  # Alt Lat Long

                self.trajectory_precise_pos.append(wpn_pos)
                self.trajectory_precise_ll_coord.append(wpn_ll)
                self.trajectory_precise_ref_time.append(time.time())

                # print(f"precise data updated for {self.lua_object_id}")
                # print(wpn_pos)

                updated_once = True

                time.sleep(0.1)

            elif q_str in cdi.export_units.keys():
                precise_dt = cdi.export_units[q_str]
                # data that cannot be obtained through precise_dt: impact point, velocity
                wpn_pos = precise_dt.unit_pos
                wpn_ll = precise_dt.unit_ll  # Alt Lat Long

                self.trajectory_precise_pos.append(wpn_pos)
                self.trajectory_precise_ll_coord.append(wpn_ll)
                self.trajectory_precise_ref_time.append(time.time())

                # print(f"precise data updated for {self.lua_object_id}")

                updated_once = True

                time.sleep(0.1)

            else:
                if updated_once:
                    cdi.active_player_weapons[self.launcher_group_id].remove(self.wpn_dt)
                    self.fin()  # finalize
                    print(f"precise pos data end for {self.lua_object_id}")
                    break
                time.sleep(0.1)

    def update(self):  # check data in cdi
        kmd_get_position = f"""
            return update_weapon_trajectory({bake_lua_weapon_object_by_id(self.lua_object_id)})
        """

        while True:
            rt = RequestDcsDebugCommand(kmd_get_position, True).send()
            if rt:
                # print("updated!")
                rt_p = rt['pos']
                rt_v = rt['vel']
                rt_t = rt['time']
                rt_l = rt['ll_coord']
                rt_m = rt['mgrs_coord']

                if 'ip' in rt.keys():
                    rt_i = rt['ip']
                    rt_il = rt['ip_ll_coord']
                    rt_im = rt['ip_mgrs_coord']

                    self.impact_point.append(rt_i)
                    self.impact_ll_coord.append(rt_il)
                    self.impact_mgrs_coord.append(rt_im)
                    # print(f"impact point: {rt_i}")

                self.trajectory_pos.append(rt_p)
                self.trajectory_velocity.append(rt_v)
                self.trajectory_ll_coord.append(rt_l)
                self.trajectory_mgrs_coord.append(rt_m)
                self.time_last_update = rt_t
                self.flight_time += 1
                print(f"weapon data updated for {self.lua_object_id}")
            else:
                print(f"weapon data end for {self.lua_object_id}")
                cdi.active_player_weapons[self.launcher_group_id].remove(self.wpn_dt)
                self.fin()  # finalize
                self.flight_time += 1
                break

            time.sleep(1)

        # print(self.trajectory_pos)


def bake_lua_weapon_object_by_id(weapon_id):  # 33555712
    lua_tbl = f"""{{['id_'] = {weapon_id},}}"""
    return lua_tbl


def init_tracker(wpn_dt):
    # launcher group id is not available
    # query id with initiator runtime id in cdi
    launcher_runtime_id = wpn_dt['launcher_object']['id_']
    q_str = f"id_{launcher_runtime_id}"
    launcher_group_id = cdi.active_players_by_unit_runtime_id[q_str].group_id
    wpn_dt['launcher_group_id'] = launcher_group_id  # add entry

    if launcher_group_id not in cdi.active_player_weapons.keys():
        cdi.active_player_weapons[wpn_dt['launcher_group_id']] = []

    cdi.active_player_weapons[wpn_dt['launcher_group_id']].append(wpn_dt)

    ntrk = WeaponTracker(wpn_dt)
    # threading.Thread(target=ntrk.update).start()
    threading.Thread(target=ntrk.update_precise_pos).start()
    # data receive end, how to report to user?
    # gp_id = wpn_dt['launcher_group_id']
    weapon_release_data.append(ntrk)


def record_hit_event(hit_event):
    cdi.hit_events.append(hit_event)


def weapon_tracker_on_event_shot(event_data):  # only check for player initiator?
    if event_data['player_control'] is True:
        # group_id = event_data['owner_group_id']  # check if this group has acmi pod installed
        weapon_data = event_data['weapon_data']

        wp_td = threading.Thread(target=init_tracker, args=[weapon_data])
        wp_td.start()
        time.sleep(0.01)

        # ammo = db.env_group_dict[group_id].lead['ammo']
        # # ammo is a list
        # for s_ammo in ammo:
        #     if s_ammo['desc']['typeName'] == 'CATM-9M':  # acmi capability, start tracking
        #         weapon_data = event_data['weapon_data']
        #
        #         wp_td = threading.Thread(target=init_tracker, args=[weapon_data])
        #         wp_td.start()
        #         time.sleep(0.01)
        #         break
        # else:  # no acmi pod, do nothing
        #     pass


def declare_weapon_tracker_event_handler():
    # print("Weapon Tracker Declare Event Handler")
    core.request.miz.dcs_event.EventHandler.SHOT[f"{plugin_name}_weapon_tracker"] = weapon_tracker_on_event_shot



if __name__ == '__main__':
    lua_wpn = bake_lua_weapon_object_by_id(33561089)
    print(lua_wpn)
    kmd_get_position = f"""
                return update_weapon_trajectory({bake_lua_weapon_object_by_id(33561089)})
            """
    print(RequestDcsDebugCommand(kmd_get_position).send())


