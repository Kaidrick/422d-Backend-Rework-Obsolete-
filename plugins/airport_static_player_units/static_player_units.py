# process player unit data
from core.request.miz.dcs_debug import RequestDcsDebugCommand
from core.game_object_control.dcs_spawn import AddStaticObject
from core.request.api.api_pull import PullSlotChanges, ApiPullHandler
from core.request.api.api_debug import RequestAPINetDostring
import threading
import time
from plugins.declare_plugins import plugin_log

plugin_name = "Airport Static Player Units"

slot_id_unit_info_dict = {}
static_player_unit_matching_dict = {}
static_prefix = "StaticPlayableAC" + " "


# TODO: handle player change slot event --> destroy the static unit
# TODO: handle player leave unit(or maybe unit dead) event --> respawn unit ? how to know what to respawn?

def get_playable_unit_data():
    # debug_cmd = """
    # local paste = {}
    # if mist.DBs.humansById then
    #     for unit_id, unit_data in pairs(mist.DBs.humansById) do
    #         paste[tostring(unit_id)] = {
    #             ['unit_name'] = unit_data.unitName,
    #             ['group_name'] = unit_data.groupName,
    #             ['type'] = unit_data.type,
    #             ['x'] = unit_data.x,
    #             ['y'] = unit_data.y,
    #             ['heading'] = unit_data.heading,
    #             ['country'] = unit_data.country,
    #             ['category'] = unit_data.category,
    #             ['onboard_num'] = unit_data.onboard_num,
    #             ['livery_id'] = unit_data.livery_id,
    #         }
    #     end
    # end
    # return paste"""
    debug_cmd = """
local JSON = require("JSON")
local res_paste = {}
for coa_name, coa_data in pairs(env.mission.coalition) do  -- parse coalition table, then generate new table

  if (coa_name == 'red' or coa_name == 'blue') and type(coa_data) == 'table' then
    if coa_data.country then --there is a country table
      for cntry_id, cntry_data in pairs(coa_data.country) do
        
        local countryName = string.lower(cntry_data.name)

        if type(cntry_data) == 'table' then	--just making sure

          for obj_type_name, obj_type_data in pairs(cntry_data) do

            if obj_type_name == "helicopter" or obj_type_name == "ship" or obj_type_name == "plane" or obj_type_name == "vehicle" or obj_type_name == "static" then --should be an unncessary check

              local category = obj_type_name

              if ((type(obj_type_data) == 'table') and obj_type_data.group and (type(obj_type_data.group) == 'table') and (#obj_type_data.group > 0)) then	--there's a group!

                for group_num, group_data in pairs(obj_type_data.group) do

                  if group_data and group_data.units and type(group_data.units) == 'table' then	--making sure again- this is a valid group
                    
                    local groupName = env.getValueDictByKey(group_data.name)  -- -> group_name
                    for unit_num, unit_data in pairs(group_data.units) do
                      if unit_data.skill == 'Client' and group_data.route.points[1].type == "TakeOffGround" then  -- is a playable unit, and is ground start, add to res_paste
                        res_paste[tostring(unit_data.unitId)] = {
                          ['unit_name'] = env.getValueDictByKey(unit_data.name),  -- -> unit_name
                          ['type'] = unit_data.type,  -- -> type
                          ['x'] = unit_data.x,
                          ['y'] = unit_data.y,
                          ['heading'] = unit_data.heading,
                          ['country'] = countryName,
                          ['category'] = category,
                          ['onboard_num'] = unit_data.onboard_num,
                          ['livery_id'] = unit_data.livery_id,
                          ['group_name'] = groupName,
                          ['group_id'] = group_data.groupId
                        }
                      end
                    end --for unit_num, unit_data in pairs(group_data.units) do
                  end --if group_data and group_data.units then
                end --for group_num, group_data in pairs(obj_type_data.group) do
              end --if ((type(obj_type_data) == 'table') and obj_type_data.group and (type(obj_type_data.group) == 'table') and (#obj_type_data.group > 0)) then
            end --if obj_type_name == "helicopter" or obj_type_name == "ship" or obj_type_name == "plane" or obj_type_name == "vehicle" or obj_type_name == "static" then
          end --for obj_type_name, obj_type_data in pairs(cntry_data) do
        end --if type(cntry_data) == 'table' then
      end --for cntry_id, cntry_data in pairs(coa_data.country) do
    end --if coa_data.country then --there is a country table
  end --if coa_name == 'red' or coa_name == 'blue' and type(coa_data) == 'table' then
end --for coa_name, coa_data in pairs(mission.coalition) do

return JSON:encode(res_paste)
    """
    return RequestAPINetDostring(debug_cmd, echo_result=True).send()
    # return RequestDcsDebugCommand(debug_cmd, True).send()


def get_airbase_id_parkings_data():
    debug_cmd = """
    local JSON = require("JSON")
    all_airbases = world.getAirbases()
    airbases_data = {}
    for _, airbase in pairs(all_airbases) do
        local parkings = airbase:getParking()
        local ab_id = airbase:getID()
        local ab_name = airbase:getName()
        env.info("ID: " .. ab_id .. " Name: " .. ab_name)
        airbases_data[tostring(ab_id)] = parkings
    end
    return JSON:encode(airbases_data)"""
    return RequestAPINetDostring(debug_cmd, echo_result=True).send()


all_playable_unit_data = get_playable_unit_data()
airbase_id_parkings_dict = get_airbase_id_parkings_data()


# find a parking position that matches the playable unit's position
def matching_playable_unit_with_parking():
    # when testing in some local missions, there might be only in air unit so no match
    try:
        for unit_id, unit_data in all_playable_unit_data.items():
            # for each unit, check all airbase parkings
            match_found = False
            for ab_id, airbase_parkings in airbase_id_parkings_dict.items():
                for parking in airbase_parkings:
                    if parking['vTerminalPos']['x'] == unit_data['x'] and parking['vTerminalPos']['z'] == unit_data['y']:
                        # print(unit_data['unit_name'], " at airport ID: ", ab_id, " found parking ", parking['Term_Index'])
                        # print("Terminal Type: ", parking['Term_Type'])

                        static_player_unit_matching_dict[unit_id] = {
                            'airdrome_id': ab_id,
                            'livery_id': unit_data['livery_id'],
                            'parking': parking['Term_Index'],
                            'parking_type': parking['Term_Type'],
                            'type': unit_data['type'],
                            'groupName': static_prefix + unit_data['group_name'],
                            'unitName': static_prefix + unit_data['unit_name'],
                            'onboard_num': unit_data['onboard_num'],
                            'x': unit_data['x'],
                            'y': unit_data['y'],
                            'heading': unit_data['heading'],
                            'country': unit_data['country']
                        }

                        # change type for low quality models to reduce lag
                        if static_player_unit_matching_dict[unit_id]['type'] == "FA-18C_hornet":
                            static_player_unit_matching_dict[unit_id]['type'] = "F/A-18C"

                        if static_player_unit_matching_dict[unit_id]['type'] == "F-5E-3":
                            static_player_unit_matching_dict[unit_id]['type'] = "F-5E"

                        if static_player_unit_matching_dict[unit_id]['type'] == "M-2000C":
                            static_player_unit_matching_dict[unit_id]['type'] = "Mirage 2000-5"

                        match_found = True

            if not match_found:  # no matching, treat as open air spawn
                static_player_unit_matching_dict[unit_id] = {
                    'airdrome_id': ab_id,
                    'livery_id': unit_data['livery_id'],
                    'parking': None,
                    'parking_type': 104,
                    'type': unit_data['type'],
                    'groupName': static_prefix + unit_data['group_name'],
                    'unitName': static_prefix + unit_data['unit_name'],
                    'onboard_num': unit_data['onboard_num'],
                    'x': unit_data['x'],
                    'y': unit_data['y'],
                    'heading': unit_data['heading'],
                    'country': unit_data['country']
                }
                if static_player_unit_matching_dict[unit_id]['type'] == "FA-18C_hornet":
                    static_player_unit_matching_dict[unit_id]['type'] = "F/A-18C"

                if static_player_unit_matching_dict[unit_id]['type'] == "F-5E-3":
                    static_player_unit_matching_dict[unit_id]['type'] = "F-5E"

                if static_player_unit_matching_dict[unit_id]['type'] == "M-2000C":
                    static_player_unit_matching_dict[unit_id]['type'] = "Mirage 2000-5"

                if static_player_unit_matching_dict[unit_id]['type'] == "F-14B":
                    static_player_unit_matching_dict[unit_id]['type'] = "F-14A"

        # print(static_player_unit_matching_dict)
    except AttributeError:
        print("debug info", "static_player_units",
              "AttributeError@def matching_playable_unit_with_parking", "no match units")


def spawn_playable_statics():
    # remove aircraft hanger or shader or anything that is controlled by flag

    for unit_id, static_data in static_player_unit_matching_dict.items():

        AddStaticObject(static_data['unitName'], static_data['type'],
                        static_data['x'], static_data['y'],
                        livery_id=static_data['livery_id'],
                        onboard_num=static_data['onboard_num'], heading=static_data['heading']).send()

        # elif static_data['parking_type'] == 72:  # TODO: add more options
        #     # print(static_data['parking_type'])
        #     kn_group = dcs_object.Group(static_data['groupName'], None, None)
        #     kn_group.uncontrolled = True
        #
        #     list_points = []
        #     start_point = dcs_object.Point(None, None, None)
        #     start_point.action = "From Parking Area"
        #     start_point.type = "TakeOffParking"
        #     start_point.airdromeId = static_data['airdrome_id']
        #
        #     list_points.append(start_point.__dict__)
        #     new_route = dcs_object.Route()
        #
        #     kn_unit = dcs_object.Unit(static_data['unitName'], None, None)
        #     kn_unit.livery_id = static_data['livery_id']
        #     kn_unit.parking = static_data['parking']
        #     kn_unit.type = static_data['type']
        #     kn_unit.name = static_data['unitName']
        #     kn_unit.onboard_num = static_data['onboard_num']
        #
        #     kn_group.add_unit(kn_unit)
        #     new_route.add_points([start_point])
        #     kn_group.route = new_route.__dict__
        #
        #     # print(kn_group.bake())
        #     AddGroup(kn_group.bake()).send()


def placeholder(pull_data):  # get slot changes
    # print("check")
    # slot_changes = PullSlotChanges().send()
    slot_change = pull_data

    # print(slot_change)
    if slot_change['slotID_FROM'] != "":  # slot_change is sth like 37_2 in multi-seat
        # check if two seater, if two seater then ignore rear seat
        plugin_log(plugin_name, f"{slot_change['slotID_player']} changed slot. "
                                f"Unit {slot_change['slotID_FROM']} is now freed. "
                                f"Respawn Unit {slot_change['slotID_FROM']}.")

        # static_player_unit_matching_dict
        try:
            static_data = static_player_unit_matching_dict[slot_change['slotID_FROM']]
            # add group or add static unit? --> depends on type? always static?
            AddStaticObject(static_data['unitName'], static_data['type'],
                            static_data['x'], static_data['y'],
                            livery_id=static_data['livery_id'],
                            onboard_num=static_data['onboard_num'], heading=static_data['heading']).send()
        except KeyError:  # not ground start unit, ignore
            print("No match, ignore despawn")

    else:  # slot_change['slotID_FROM'] is ""
        # print("from \"\" to \"\"? disconnect?")
        pass

    if slot_change['slotID_TO'] != "":
        plugin_log(plugin_name, f"{slot_change['slotID_player']} changed slot. "
                                f"Destroy Unit {slot_change['slotID_TO']}. "
                                f"Unit {slot_change['slotID_TO']} is now occupied.")

        # static_player_unit_matching_dict[unitId] --> Unit.getByName():destroy() ?
        try:
            unit_info = static_player_unit_matching_dict[slot_change['slotID_TO']]
            # print(unit_info)
            unit_name = unit_info['unitName']
            msg = f"""
                                    local success, data = pcall(StaticObject.getByName, '{unit_name}')
                                        if success then
                                            if data:isExist() then
                                                data:destroy()
                                            end
                                        end
                                """
            RequestDcsDebugCommand(msg).send()
        except KeyError:  # no match found, must not be ground start, ignore
            print("No match - Parking start unit, ignore")

    # for slot_change in slot_changes:  # from to is actually the game unit id for some reason
    #     # print(slot_change)
    #     if slot_change['slotID_FROM'] != "":  # slot_change is sth like 37_2 in multi-seat
    #         # check if two seater, if two seater then ignore rear seat
    #         plugin_log(plugin_name, f"Unit {slot_change['slotID_FROM']} is now freed")
    #         plugin_log(plugin_name, f"Respawn Unit {slot_change['slotID_FROM']}")
    #
    #         # static_player_unit_matching_dict
    #         try:
    #             static_data = static_player_unit_matching_dict[slot_change['slotID_FROM']]
    #             # add group or add static unit? --> depends on type? always static?
    #             AddStaticObject(static_data['unitName'], static_data['type'],
    #                             static_data['x'], static_data['y'],
    #                             livery_id=static_data['livery_id'],
    #                             onboard_num=static_data['onboard_num'], heading=static_data['heading']).send()
    #         except KeyError:  # not ground start unit, ignore
    #             print("No match, ignore despawn")
    #
    #     else:  # slot_change['slotID_FROM'] is ""
    #         # print("from \"\" to \"\"? disconnect?")
    #         pass
    #
    #     if slot_change['slotID_TO'] != "":
    #         plugin_log(plugin_name, f"Destroy Unit {slot_change['slotID_TO']}")
    #         plugin_log(plugin_name, f"Unit {slot_change['slotID_TO']} is now occupied")
    #
    #         # static_player_unit_matching_dict[unitId] --> Unit.getByName():destroy() ?
    #         try:
    #             unit_info = static_player_unit_matching_dict[slot_change['slotID_TO']]
    #             # print(unit_info)
    #             unit_name = unit_info['unitName']
    #             msg = f"""
    #                             local success, data = pcall(StaticObject.getByName, '{unit_name}')
    #                                 if success then
    #                                     if data:isExist() then
    #                                         data:destroy()
    #                                     end
    #                                 end
    #                         """
    #             RequestDcsDebugCommand(msg).send()
    #         except KeyError:  # no match found, must not be ground start, ignore
    #             print("No match - Parking start unit, ignore")

    # all_slots = RequestSlotInfo().send()
    # for slot_id, slot in enumerate(all_slots):  # lua table index starts at 1 not 0
    #     if slot['role'] == 'pilot':
    #         slot_id_unit_info_dict[slot_id + 1] = slot
    # print(slot_id_unit_info_dict)

    # at server start, spawn all static aircraft

    # start a thread to pull changed slot from control api
    # check changed slot id --> find unit --> find static group/static object
    # pre-match slot id and statics units for display?

    # on slot change, static unit:destroy()

    # on how to know if a slot in no longer occupied? check PullSlotChanges from to


# ApiPullHandler.SLOT_CHANGE['playable_static_aircraft_spawn_control'] = placeholder


def include_static_player_units():
    matching_playable_unit_with_parking()
    spawn_playable_statics()

    # include_static_player_units()

    ApiPullHandler.SLOT_CHANGE['playable_static_aircraft_spawn_control'] = placeholder

    # placeholder()
    #
    # def timer():
    #     while True:
    #         placeholder()
    #         time.sleep(0.1)
    #
    # s1 = threading.Thread(target=timer)
    # s1.start()


def declare():
    pass
