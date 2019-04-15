import time
import threading
import core.data_interface as cdi
import numpy as np
from core.request.miz.dcs_event import EventHandler
from core.spark import SparkHandler
from core.request.miz.dcs_debug import RequestDcsDebugCommand
from core.request.miz.dcs_message import RequestDcsMessageForGroup
from .data_interface import missiles_in_control, recent_missiles, clean_obsolete_data, log_missile
from .range_protection import player_tracker, protect_new_player_spawn
from .missile_data import missile_get_position
from .target_data import get_target_position_lua_object
import core.utility.utils as utils
from .missile import SurfaceToAirMissile, MissileControlRelease
from .missile_training_announcer import announce_simulation_launch, placeholder_name_for_this_report_function
import gettext

_ = gettext.gettext


plugin_name = "Missile Trainer"


def unit_object_by_runtime_id(runtime_id):
    for name, unit_obj in {**cdi.active_players_by_name, **cdi.other_units_by_name}.items():
        if unit_obj.runtime_id == runtime_id:
            return unit_obj

    # after search, none found
    return None


def batch_radar_target_update(batch_object_id: list):
    pass  # TODO: check if necessary? and launcher may not be the radar, need to get radar unit


def batch_tracking_target_update(batch_object_id: list):
    bake_list = "local batch_missile_objects = {}\n"
    for msl_obj_id in batch_object_id:
        msl_obj_lua_str = utils.bake_object_id(msl_obj_id)
        bake_list += f"table.insert(batch_missile_objects, {msl_obj_lua_str})\n"

    psr = f""" -- still need to use protected call here, or dcs will freeze
    
    -- batch in lua code here:
    
    local res_targets = {{}}
    for _, missile_obj in pairs(batch_missile_objects) do
        success, res = pcall(
            function() return Weapon.getTarget(missile_obj) end
        )
        if success then
            res_targets['id_' .. missile_obj['id_']] = res
        else
            res_targets['id_' .. missile_obj['id_']] = nil  -- return nil as target
        end
    end
    
    -- after loop is done and all obj is process and paired with a target
    return res_targets
    
    """
    cmd = bake_list + psr
    # print(cmd)
    res = RequestDcsDebugCommand(cmd, True).send()  # returns a list # {'id_': 16880129}
    return res


def missile_target_updater():  # a tracker to update all missile's target for missile in control
    while True:
        missile_p_id = []
        for p_id in missiles_in_control.keys():
            p_id = p_id[3:]
            missile_p_id.append(p_id)

        res_target_dict = batch_tracking_target_update(missile_p_id)
        if res_target_dict:
            for missile_id_name, missile_target in res_target_dict.items():
                try:
                    kn_missile = missiles_in_control[missile_id_name]
                except KeyError:
                    print(f"Missile {missile_id_name} no longer exists in miz?")
                else:
                    tracking_target_id = str(kn_missile.current_target.runtime_id)
                    current_target_id = str(missile_target['id_'])
                    # print("lua target: ", missile_target, "tracking target: ", tracking_target)
                    if tracking_target_id != current_target_id:  # target change
                        try:
                            current_target_object = unit_object_by_runtime_id(current_target_id)
                        except KeyError:
                            current_target_object = None
                        kn_missile.target_change(current_target_object)
                    else:  # still tracking the same target
                        pass

        time.sleep(2)  # update all target every 2 seconds


def missile_get_target(wpn_object_id: int):  # single request style target getter
    cmd = f"""
    success, res = pcall(function() return Weapon.getTarget({utils.bake_object_id(wpn_object_id)}) end)
    if success then return res else return nil end
    """
    res = RequestDcsDebugCommand(cmd, True).send()  # {'id_': 16880129}
    return res


def control_missile(missile_obj):
    # add missile to missiles_in_control dict
    missiles_in_control['id_' + str(missile_obj.wpn_object_id)] = missile_obj
    print(f"SAM Trainer is tracking missile {missile_obj}, runtime id {missile_obj.wpn_object_id}")


def release_control_missile(missile_obj):
    # del entry
    del missiles_in_control['id_' + str(missile_obj.wpn_object_id)]
    log_missile(missile_obj)
    print(f"SAM Trainer released missile {missile_obj}, runtime id {missile_obj.wpn_object_id}")


def missile_controller():
    gate = 0  # what is this? steps for placeholder function and clean obsolete data?
    while True:
        missiles_in_control_copy = missiles_in_control.copy()
        for missile_id, missile_object in missiles_in_control_copy.items():
            keep_control = missile_object.control_step()  # run method to get missile current position
            if not keep_control:
                release_control_missile(missile_object)
        # if done
        if gate >= 5:
            placeholder_name_for_this_report_function()
            clean_obsolete_data()
            gate = 0

        gate += 1

        time.sleep(1)  # update all every 1 second


def report_simulation_result(target, release_reason):
    target_group_id = target.group_id
    msg = ""
    if MissileControlRelease.OUT_MANEUVER == release_reason:
        msg = "Missile energy depleted!"
    elif MissileControlRelease.DECOY == release_reason:
        msg = "Missile decoyed!"
    elif MissileControlRelease.LOCK_BREAK == release_reason:
        msg = "Missile Lock Failed!"
    elif MissileControlRelease.SAFE_DISTANCE == release_reason:
        msg = "Missile Hit!"

    RequestDcsMessageForGroup(target_group_id, msg).send()


def missile_launch_handle(event_data):  # do things at missile launch
    # TODO: only works with AI launched SAM at the moment!
    if not event_data['player_control'] and event_data['weapon_data']['desc']['missileCategory'] == 2:
        # interpret event data
        # should be able to handle all kinds of missiles from all sources, as long as target is in selected Range area
        launcher_runtime_id = event_data['initiator_runtime_id']  # without 'id_' prefix
        launcher_type = event_data['initiator_type']
        wpn_type_name = event_data['weapon_data']['desc']['typeName']
        wpn_object_id = event_data['weapon_data']['object']['id_']

        # no need to know target, only need to know weapon launch
        # but need to send message to player?

        new_missile = SurfaceToAirMissile(launcher_runtime_id, wpn_object_id, event_data['weapon_data'])
        control_missile(new_missile)

        new_missile_target = missile_get_target(wpn_object_id)  # returns a dict like {'id_': 16880129}
        if new_missile_target:  # if target exists
            try:  # TODO: what if missile target is a anti-radiation missile or AGM?
                target = unit_object_by_runtime_id(new_missile_target['id_'])
            except KeyError:  # target does no exist?
                print(__file__, "def missile_launch_hanlde", "checking new missile target",
                      "target does not exist in data interface")
            else:
                announce_simulation_launch(event_data, target)

            print("ecs missile launch!", launcher_type, wpn_type_name)


    # send notice
    # if AI controlled SAM launch, should have a target
    # if AI controlled AGM launch, maybe a target?
    # if AI controlled A2A launch, maybe a target, what about AIM-120?
    # if player controlled A2A launch, maybe a target
    # if player controlled AGM launch, maybe a target? what if target is in air?


def declare():
    threading.Thread(target=player_tracker).start()  # tracker on timer to set player visibility

    # range missile monitors:
    threading.Thread(target=missile_controller).start()
    threading.Thread(target=missile_target_updater).start()

    EventHandler.SHOT['nttr_missile_trainer_check_sam_launch'] = missile_launch_handle
    SparkHandler.PLAYER_SPAWN['nttr_missile_trainer_protect_new_player_spawn'] = protect_new_player_spawn

