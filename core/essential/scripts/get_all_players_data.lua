local players_unit = coalition.getPlayers(2)  -- get all blue players for the moment, may need to change this later
local res = {}
for _, player_unit in pairs(players_unit) do  -- iterate through every player unit to collect data
    local player_dt = {}
    player_dt.name = player_unit:getPlayerName()
    player_dt.unit_name = player_unit:getName()
    player_dt.unit_id = player_unit:getID()
    player_dt.unit_runtime_id_name = 'id_' .. player_unit.id_

    res[player_dt.name] = player_dt
end
return res
