local ofsmiz = {}
net.log("Loading OFSMIZ interface")

local PORT = PORT or 3010
local DATA_TIMEOUT_SEC = DATA_TIMEOUT_SEC or 0.1

package.path = package.path .. ";./LuaSocket/?.lua"
package.path = package.path .. ";./Scripts/?.lua"
package.cpath = package.cpath .. ";./LuaSocket/?.dll"


local socket = require("socket")
--local JSON = loadfile("Scripts\\JSON.lua")
local JSON = require("JSON")
--local inspect = require("inspect")


local tcp
local client = nil
local server = nil

local offline_testing = true  -- if running on local machine

local do_step = false


local HANDLE = {}
HANDLE.MESSAGE = "net_message"  -- maybe send a chat message?
HANDLE.ACTION = "net_action"  -- kick? or something
HANDLE.QUERY = "net_query"  -- query player info?
HANDLE.EVENT = "net_event"
HANDLE.LOG = "net_log"  -- write to log
HANDLE.DEBUG = "net_debug"
HANDLE.PULL = "net_pull"  -- for example, pull player entered slot

local PULL = {}
PULL.SLOT_CHANGE = "slot_changes"
PULL.CHAT_CMD = "chat_cmd"


--[[
██████╗  █████╗ ████████╗ █████╗      ██████╗ ██████╗ ███╗   ██╗████████╗ █████╗ ██╗███╗   ██╗███████╗██████╗ 
██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗    ██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔══██╗██║████╗  ██║██╔════╝██╔══██╗
██║  ██║███████║   ██║   ███████║    ██║     ██║   ██║██╔██╗ ██║   ██║   ███████║██║██╔██╗ ██║█████╗  ██████╔╝
██║  ██║██╔══██║   ██║   ██╔══██║    ██║     ██║   ██║██║╚██╗██║   ██║   ██╔══██║██║██║╚██╗██║██╔══╝  ██╔══██╗
██████╔╝██║  ██║   ██║   ██║  ██║    ╚██████╗╚██████╔╝██║ ╚████║   ██║   ██║  ██║██║██║ ╚████║███████╗██║  ██║
╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
--]]

NetPlayerInfoById = {}
NetPlayerInfo = {}  -- current connected player list
-- lua will update this NetPlayerInfo table
-- when a player connect, this an entry is added.
-- when a player disconnect, an entry will be removed.
-- we want to know the settings of this player
-- send ucid to python to search for user data  --> pull to python
-- if data exist return settings, if not set default

NetSlotInfo = {}
--[[
[15] = {
	action = "From Ground Area",
	callsign = { 1, 1, 1, name = "Enfield11"},
	countryName = "USA",
	groupName = "F-5E-3 (02) Sn: 761527",
	groupSize = 1,
	onboard_num = "04",
	role = "pilot",
	task = "CAP",
	type = "F-5E-3",
	unitId = "760"
}
--]]
NetPulls = {}
CmdPulls = {}

function bake_pull(p)
	local pull_type = p[1]
	local echo_content = p[2]

	echo_content.type = pull_type  -- 1 is slot changes, 2 is chat cmd
	
	NetPulls[#NetPulls+1] = echo_content
	
	echo_content = nil
	pull_type = nil
end


local function has_value (tab, val)
    for index, value in ipairs(tab) do
        if value == val then
            return true
        end
    end

    return false
end


local function find_player_mission_group_id(player_id)
	-- check NetPlayerInfoById with playerID
	if NetPlayerInfoById[player_id] then
		return NetPlayerInfoById[player_id]
	end
end


function dostring_api_env(s)
	local f, err = loadstring(s)
	if f then
		return true, f()
	else
		return false, err
	end
end


local function add_dummy_players_for_testing()
	NetPlayerInfoById[1] = {
			ipaddr = '210.151.40.233:10308',  -- ipaddr
			name = "Kaidrick",  -- name
			ucid = '95a081bb351128cf962f13e355a8326b',  -- ucid
			playerID = 1  -- id
	}

	NetPlayerInfo['95a081bb351128cf962f13e355a8326b'] = {
			ipaddr = '210.151.40.233:10308',  -- ipaddr
			name = "Kaidrick",  -- name
			ucid = '95a081bb351128cf962f13e355a8326b',  -- ucid
			playerID = 1  -- id
	}
	
	NetPlayerInfo['5f37820d31ec4a198f0c09028d95d4f4'] = {
		ipaddr = '51.245.26.191:10308',  -- ipaddr
		name = "Kaidrick",  -- name
		ucid = '5f37820d31ec4a198f0c09028d95d4f4',  -- ucid
		playerID = 2  -- id
	}
	
	NetPlayerInfo['8cf779e20008404294d0fce7df0732ab'] = {
		ipaddr = '74.74.167.31:10308',  -- ipaddr
		name = "very stupid name!",  -- name
		ucid = '8cf779e20008404294d0fce7df0732ab',  -- ucid
		playerID = 3  -- id
	}
	
	NetPlayerInfo['606d3d03d4ef4941858c2a533e2ef6e9'] = {
		ipaddr = '168.199.164.94:10308',  -- ipaddr
		name = "河马！",  -- name
		ucid = '606d3d03d4ef4941858c2a533e2ef6e9',  -- ucid
		playerID = 4  -- id
	}
end



function process_request(request)  -- runs request from API Request
	local success, err = false, nil
	
	if request.handle == HANDLE.QUERY then
		if request.type == "player_info" then
			return NetPlayerInfo
		elseif request.type == "slot_info" then
			return NetSlotInfo	
		end
		
	elseif request.handle == HANDLE.DEBUG then
		if request.type == "mem" then
			local mem = {}
			mem.size = collectgarbage('count')
			mem.time = os.time()
			
			return mem
		elseif request.type == "net_dostring" then
			local res = net.dostring_in(request.env, request.content)  -- res is a string
			-- 'server': holds the current mission when multiplayer? server only
			-- 'config': the state in which $INSTALL_DIR/Config/main.cfg is executed, as well as $WRITE_DIR/Config/autoexec.cfg
            --           used for configuration settings
			-- 'mission': holds current mission
			-- 'export': runs $WRITE_DIR/Scripts/Export.lua and the relevant export API
			
			-- check if res is a json string or a normal string
			local success, result = pcall(function() return JSON:decode(res) end)
			if success then  -- is json string
				return result
			else  -- normal string
				return res
			end
		
		elseif request.type == "api_loadstring" then
			local returned, result = dostring_api_env(request.content)
			return result
		end
	elseif request.handle == HANDLE.PULL then
		local tbs = NetPulls
		NetPulls = {}
		
		return tbs
	
		-- if request.type == PULL.SLOT_CHANGE then
			-- local tbs = NetPulls
			-- NetPulls = {}
		
			-- return tbs
		-- elseif request.type == PULL.CHAT_CMD then
			-- local tbs = CmdPulls
			-- CmdPulls = {}
			
			-- return tbs
		-- end
	elseif request.handle == HANDLE.MESSAGE then
		net.send_chat_to(request.message, request.player_id)
	end
	
end


---[[
local function checkJSON(jsonstring, code)
  if code == "encode" and type(JSON:encode(jsonstring)) ~= "string" then
    error("encode expects a string after function")
  end
  
  if code == "decode" and type(jsonstring) ~= "string" then
    error("decode expects string")
  end
end
--]]


local function step()
	if server then
		server:settimeout(0.001)  -- give up if no connection
		client = server:accept()  -- accept client
		
		if client then  -- if client not nil, connection established
			--client:settimeout(0.001)
			local line, err = client:receive()
			if not err then
				--env.info(line)
				local success, request = pcall(
					function()
						return JSON:decode(line)
					end
				)
				if success then  -- run request here
					-- run_request
					local result, request_err = process_request(request)
					
					-- after request
					local bytes, status, lastbyte = client:send(JSON:encode(result) .. '\n')
				else
					env.info(request)  -- log error
				end
			end
			
			client:close()  -- done, close connection
			
		else  -- no client connection
			-- do nothing
		end
	end
end


-----------------------------------------------------------------------------------------

function ofsmiz.onSimulationStart()
	log("Starting DCS API CONTROL server")
	
	server = assert(socket.bind("127.0.0.1", PORT))
	server:settimeout(0.001)
	local ip, port = server:getsockname()
	net.log("DCS API Server: Started on Port " .. port .. " at " .. ip)
end


local step_frame_count = 0
function ofsmiz.onSimulationFrame()
	if do_step then
		step_frame_count = step_frame_count + 1
		if step_frame_count == 1 then -- at every 10th frame
			--step()
			--net.log("this is frame: " .. step_frame_count .. " at " .. os.time())
		
			-- call step if in game env?
			local success, error = pcall(step)
			if not success then
				net.log("Error: " .. error)
			end
		
			step_frame_count = 0
		
		end
	end
end

function ofsmiz.onSimulationStop()
	server:close()
	net.log("API CONTROL SERVER TERMINATED")
end

function ofsmiz.onNetConnect(localPlayerID)  -- only if isServer()
	-- this is where the netview is initiated?

	net.log("onNetConnect")
	-- map slot and id and things
	NetSlotInfo = {}  -- reset NetSlotInfo
	-- local coals = DCS.getAvailableCoalitions() --> table { [coalition_id] = { name = "coalition name", } ... }
	local slots = DCS.getAvailableSlots("blue")
	for slot_id, slot_info in ipairs(slots) do
		NetSlotInfo[slot_id] = {
			["action"] = slot_info.action,
			["countryName"] = slot_info.countryName,
			["groupName"] = slot_info.groupName,
			["groupSize"] = slot_info.groupSize,
			["onboard_num"] = slot_info.onboard_num,
			["role"] = slot_info.role,
			["type"] = slot_info.type,
			["task"] = slot_info.task,
			["unitId"] = slot_info.unitId,
		}
	end
	
	--[[
	[15] = {
	action = "From Ground Area",
	callsign = { 1, 1, 1, name = "Enfield11"},
	countryName = "USA",
	groupName = "F-5E-3 (02) Sn: 761527",
	groupSize = 1,
	onboard_num = "04",
	role = "pilot",
	task = "CAP",
	type = "F-5E-3",
	unitId = "760"
}
	--]]
	
	do_step = true -- onSimulationFrame can start step()
end


function ofsmiz.onPlayerChangeSlot(id)

end

function ofsmiz.onNetDisconnect(reason_msg, err_code)
	net.log("onNetDisconnect")
	do_step = false -- onSimulationFrame can start step()
end

---[[
function ofsmiz.onPlayerTryConnect(addr, name, ucid, playerID)  -- check if on black list?
	if true then  -- if player is not on blacklist
		-- do I have info on this ucid? check for ucid key
		net.log("passed blacklist check")
		local new_conn_info = {}
		new_conn_info.ipaddr = addr
		new_conn_info.name = name
		new_conn_info.ucid = ucid
		new_conn_info.playerID = playerID
		
		-- check if user data exists?
		NetPlayerInfo[ucid] = new_conn_info  -- key is ucid
		NetPlayerInfoById[playerID] = new_conn_info  -- key is player id in the net env
		--]]
		net.log("New Connection: " .. new_conn_info.ipaddr .. ", name: " .. new_conn_info.name .. ", ucid: " .. new_conn_info.ucid)
		return true
	else
		return false, "Banned"
	end
end

function ofsmiz.onPlayerTryChangeSlot(playerID, side, slotID) -- -> true | false
	net.log("onPlayerTryChangeSlot")
	
	-- assuming the id is actually the slot_id
	local player_info = net.get_player_info(playerID) --> client language can be get here
	
	NetPlayerInfoById[playerID].slotID = slotID
	
	local p = {}
	p.slotID_TO = slotID
	p.slotID_FROM = player_info.slot
	p.slotID_player = player_info.name
	
	local rt = {
		PULL.SLOT_CHANGE,
		p,
	}
	bake_pull(rt)
	
	--NetPlayerInfo[player_info.id] = player_info
	--net.log(player_info.id)
	--net.log(player_info.name)
	--net.log(player_info.side)  -- side before changing slot, 0 is neutral
	--net.log(player_info.slot)  -- slot number before changing, "" is observer list
	--net.log(player_info.ucid)
	--net.log(player_info.ipaddr)  -- doesn't return localhost ip for local player (server)
	net.log("End onPlayerTryChangeSlot")
    return true
end

-- TODO: update this table when backend starts or on need
local chat_cmd_syntax = {
	'/info', '/信息', '/xinxi', '/chaxun', '/查询',  -- information query related
	
	'/roll',  -- roll dice
	
	'/ll', '/latlon', '/经纬',  -- coord conversion: mgrs to ll
	'/mgrs', '/utm', '/战术', '战术坐标',  -- coord conversion: convert ll to mgrs
	'/lo', '/xy', '/vec3', -- coord conversion: ll to Lo

	
	'/bra', '/dir',  -- direction
	
	'/bullseye', '/bulls', -- to bulls coord
	
	'/meter', '/meters', '/米', '/m',  -- unit conversion: to meter
	'/ft', '/feet', '/foot', '/英尺',  -- unit conversion: to meter
	'/nm', '/mile', '/miles', '/海里', -- unit conversion: to nautical mile
	'/km', '/kilometer', '/kilometers', '/千米',  -- unit conversion: to kilometers
	'/kt', '/kts', '/knot', '/knots', '/节',  -- unit conversion: to knots
	'/kmh', '/kmph', '/千米时', '/千米/时',  -- unit conversion: to kilometers per hour
	
	'/kg', '/kgs', '/kilogram', '/kilograms', '/千克', '/公斤',  -- unit conversion: to kilograms
	'/lb', '/lbs', '/pound', '/pounds', '/磅', '/英镑',  -- unit conversion: to pounds
	
	'/help', '/帮助', '/cmd', '/commands', '/cmds',  -- help message
	
	'/admin',  -- admin options
	
	'/debug',  -- debug options
}

function ofsmiz.onPlayerTrySendChat(playerID, msg, all) -- -> filteredMessage | "" - empty string drops the message
    -- check if this message is a valid chat command
	-- that means, if it has a leading keyword in the in command list
	-- if it is has such keyword, bake command and send to python, else return the orginal msg
	
	-- somehow the local server chat message is also catched
	
	local words = {}
	for word in msg:gmatch("%S+") do words[#words + 1] = word end
	-- check list contain the inital word
	local check_word = string.lower(words[1])
	if has_value(chat_cmd_syntax, check_word) then  -- contains 
		-- bake pull here, return "" to drop the message
		local p = {}
		p.check_word = check_word
		p.msg = msg
		p.player_id = playerID
		
		local rt = {
			PULL.CHAT_CMD,
			p,
		}
		bake_pull(rt)
		
		return ""
	else  -- no match, regular msg, return
		return msg
	end
	
	return msg
end

function ofsmiz.onPlayerDisconnect(id, err_code)  -- won't call for local player
	local p = {}
	p.slotID_TO = ""
	p.slotID_FROM = NetPlayerInfoById[id].slotID or ""
	p.slotID_player = NetPlayerInfoById[id].name or ""
	
	local rt = {
		PULL.SLOT_CHANGE,
		p,
	}
	bake_pull(rt)
	
	ucid = NetPlayerInfoById[id].ucid
	
	if not offline_testing then
		NetPlayerInfoById[id] = nil
		NetPlayerInfo[ucid] = nil
	end
end


function ofsmiz.onPlayerStop(id)
	net.log("player " .. id .. " stopped.")
	
	local p = {}
	p.slotID_TO = ""
	p.slotID_FROM = NetPlayerInfoById[id].slotID or ""
	p.slotID_player = NetPlayerInfoById[id].name or ""
	
	local rt = {
		PULL.SLOT_CHANGE,
		p,
	}
	bake_pull(rt)
	
    ucid = NetPlayerInfoById[id].ucid
	
	if not offline_testing then
		NetPlayerInfoById[id] = nil
		NetPlayerInfo[ucid] = nil
	end	
end
--]]





-- initialize NetPlayerInfo if offline_testing
if offline_testing then
	add_dummy_players_for_testing()
end

-- for k,v in pairs(net) do
	-- net.log("net." .. k)
-- end
-- for k,v in pairs(DCS) do
	-- net.log("DCS." .. k)
-- end


DCS.setUserCallbacks(ofsmiz)  -- here we set our callbacks