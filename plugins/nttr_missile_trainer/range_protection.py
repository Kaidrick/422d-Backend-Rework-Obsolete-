import core.data_interface as cdi
from core.game_object_control.dcs_set_command import SetInvisible
from .data_interface import missile_training_range
import time
from core.request.miz.dcs_debug import RequestDcsDebugCommand


def unit_object_by_runtime_id_name(runtime_id_name):
    for name, unit_obj in {**cdi.active_players_by_name, **cdi.other_units_by_name}.items():
        if unit_obj.runtime_id_name == runtime_id_name:
            return unit_obj

    # after search, none found
    return None


def protect(player_name):  # set all aircraft to invisible when spawn FIXME: all aircraft, player only now
    # test set invisible, should only attack once
    target_unit = cdi.active_players_by_name[player_name]
    player_group_name = target_unit.player_group_name
    SetInvisible(player_group_name).send()
    # print(f"set {unit_runtime_id_name} invisible")
    target_unit.invisible_to_ai = True
    print(f"Set {player_name} Invisible")


def unprotect(player_name):
    # test set invisible, should only attack once
    target_unit = cdi.active_players_by_name[player_name]
    player_group_name = target_unit.player_group_name
    SetInvisible(player_group_name, False).send()
    print(f"Set {player_name} Visible")
    # print(f"undo {unit_runtime_id_name} invisible")
    target_unit.invisible_to_ai = False


def protect_new_player_spawn(spk_dt):
    player_name = spk_dt['data']['name']
    # protect(player_name)


def player_tracker():  # track all player position (if in range)
    # SetInvisible does not work in multi-player

    # need to switch on or off all missiles AI based on whether ECS range has a player in it

    # how do you find all missile launcher group?
    # tree: wsType_SAM = 16 (Level 2)
    # iterate through cdi other units and find a matching unit_name that has the specific wsType

    while True:
        sam_group_names = set()
        ecs_range_occupied = False

        for unit_name, unit_object in cdi.other_units_by_name.items():
            # for this unit, check export_omni for wsType
            for runtime_id_name, unit_dt in cdi.export_omni.items():
                if 'UnitName' in unit_dt.keys() and unit_name == unit_dt['UnitName']:
                    ws_type = unit_dt['Type']
                    if ws_type['level2'] == 16:  # SAM
                        sam_group_names.add(unit_object.group_name)
                        break  # found for this unit, check next other unit object

        # print(sam_group_names)

        for player_name, player_dt in cdi.active_players_by_name.items():
            p_as = player_dt.get_airspace()
            if p_as and p_as in missile_training_range:

                # if at least one player is in missile training range, set
                ecs_range_occupied = True
                break

                # if player is in training range, unprotect
                # if player is not in training range, protect
                # unprotect(runtime_id)

                # -- if player is in a defined airspace
                # -- is player already registered to this airspace?

            #     if player_dt.invisible_to_ai:  # player is invisible to AI, unprotect
            #         unprotect(player_name)
            #         player_dt.invisible_to_ai = False
            #     else:  # player is already unprotected, do nothing
            #         pass
            #
            # else:  # not in range, do nothing. but if player enters range then leave, need to re-protect
            #     # protect(runtime_id)
            #     if not player_dt.invisible_to_ai:
            #         protect(player_name)
            #     else:  # player is already protected
            #         pass

        # if occupied flag has not switch to True

        # check if range has at least on player
        if ecs_range_occupied:  # switch on SAM AI
            for gp_name in sam_group_names:
                switch_on_ai = f"""
                    Group.getByName('{gp_name}'):getController():setOnOff(true)
                """
                RequestDcsDebugCommand(switch_on_ai).send()

            # print("range_protection.py", "set AI ON")

        else:  # not occupied, switch off SAM AI
            for gp_name in sam_group_names:
                switch_on_ai = f"""
                    Group.getByName('{gp_name}'):getController():setOnOff(false)
                """
                RequestDcsDebugCommand(switch_on_ai).send()

            # print("range_protection.py", "set AI OFF")

        time.sleep(5)

    # use an airspace change event?
