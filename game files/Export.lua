package.path = package.path .. ";./LuaSocket/?.lua"
package.path = package.path .. ";./Scripts/?.lua"
package.cpath = package.cpath .. ";./LuaSocket/?.dll"


local socket = require("socket")
local JSON = require("JSON")
--local inspect = require("inspect")

local PORT = PORT or 3011
local DATA_TIMEOUT_SEC = DATA_TIMEOUT_SEC or 0.01

local default_output_file = nil


local client = nil
local server = nil


local function checkJSON(jsonstring, code)
  if code == "encode" and type(JSON:encode(jsonstring)) ~= "string" then
    error("encode expects a string after function")
  end
  
  if code == "decode" and type(jsonstring) ~= "string" then
    error("decode expects string")
  end
end


function dostring_export_env(s)
	local f, err = loadstring(s)
	if f then
		return true, f()
	else
		return false, err
	end
end


local function step()
	if server then
		server:settimeout(0)
		client = server:accept()
		
		if client then
			local line, err = client:receive()
			if not err then
				local success, request = pcall(
					function()
						return JSON:decode(line)
					end
				)
				if success then
					local result, request_err = process_request(request)
					
					local bytes, status, lastbyte = client:send(JSON:encode(result) .. '\n')
				else
					net.log(request)
				end
			end
			
			client:close()
		end
	
	else  -- no client connection
		
	end
end



--[[
██████╗ ███████╗ ██████╗ ██╗   ██╗███████╗███████╗████████╗
██╔══██╗██╔════╝██╔═══██╗██║   ██║██╔════╝██╔════╝╚══██╔══╝
██████╔╝█████╗  ██║   ██║██║   ██║█████╗  ███████╗   ██║   
██╔══██╗██╔══╝  ██║▄▄ ██║██║   ██║██╔══╝  ╚════██║   ██║   
██║  ██║███████╗╚██████╔╝╚██████╔╝███████╗███████║   ██║   
╚═╝  ╚═╝╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚══════╝╚══════╝   ╚═╝   
--]]

HANDLE = {}
HANDLE.QUERY = "data_query"
HANDLE.DEBUG = "data_debug"

function process_request(request)  -- runs request from Export Request
	local success, err = false, nil
	
	if request.handle == HANDLE.QUERY then
		if request.type == "units" then
			local all_objects = LoGetWorldObjects(request.type)
			local res = {}
			for object_id, object_data in pairs(all_objects) do
				res["id_" .. object_id] = object_data
			end
			
			all_objects = nil
			
			return res
		elseif request.type == "ballistic" then
			local all_ballistics = LoGetWorldObjects(request.type)
			local res = {}
			for bal_id, bal_data in pairs(all_ballistics) do
				res["id_" .. bal_id] = bal_data
			end
			
			all_ballistics = nil
			
			return res
		elseif request.type == "airdromes" then
			local all_aidromes = LoGetWorldObjects(request.type)
			local res = {}
			for ab_id, ab_data in pairs(all_aidromes) do
				res["id_" .. ab_id] = ab_data
			end
			return res
			
		elseif request.type == "omni" then -- combine all export data
			local all_objects = LoGetWorldObjects("units")
			
			local all_ballistics = LoGetWorldObjects("ballistic")
			
			local res = {}
			
			for object_id, object_data in pairs(all_objects) do
				res["id_" .. object_id] = object_data
				res['id_' .. object_id]._timestamp = socket.gettime()
			end
			
			for bal_id, bal_data in pairs(all_ballistics) do
				res["id_" .. bal_id] = bal_data
				res["id_" .. bal_id]._timestamp = socket.gettime()
			end
			
			return res
		end
		
	elseif request.handle == HANDLE.DEBUG then
		if request.type == "mem" then
			local mem = {}
			mem.size = collectgarbage('count')
			mem.time = os.time()
			
			return mem
		
		elseif request.type == "export_loadstring" then
			local returned, result = dostring_export_env(request.content)
			return result
		
		end
	end
end


--[[
███████╗██╗  ██╗██████╗  ██████╗ ██████╗ ████████╗
██╔════╝╚██╗██╔╝██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝
█████╗   ╚███╔╝ ██████╔╝██║   ██║██████╔╝   ██║   
██╔══╝   ██╔██╗ ██╔═══╝ ██║   ██║██╔══██╗   ██║   
███████╗██╔╝ ██╗██║     ╚██████╔╝██║  ██║   ██║   
╚══════╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   
--]]


function LuaExportStart()
	log("Starting DCS EXPORT DATA server")
	server = assert(socket.bind("127.0.0.1", PORT))
	server:settimeout(0)
	local ip, port = server:getsockname()
	log("DCS EXPORT DATA Server: Started on Port " .. port .. " at " .. ip)
	
end

function LuaExportBeforeNextFrame()
	
end

function LuaExportAfterNextFrame() -- run step function here?

end

function LuaExportStop()
-- Works once just after mission stop.
-- Close files and/or connections here.
-- 1) File
   if default_output_file then
	  default_output_file:close()
	  default_output_file = nil
   end
-- 2) Socket
--	socket.try(c:send("quit")) -- to close the listener socket
--	c:close()
	server:close()
	log("API EXPORT DATA SERVER TERMINATED")
end

function LuaExportActivityNextEvent(t)
	local tNext = t
	tNext = tNext + 0.01
	
	step()

	return tNext
end

--[[

-- Lock On supports Lua coroutines using internal LoCreateCoroutineActivity() and
-- external CoroutineResume() functions. Here is an example of using scripted coroutine.

Coroutines = {}	-- global coroutines table
CoroutineIndex = 0	-- global last created coroutine index

-- This function will be called by Lock On model timer for every coroutine to resume it
function CoroutineResume(index, tCurrent)
	-- Resume coroutine and give it current model time value
	coroutine.resume(Coroutines[index], tCurrent)
	return coroutine.status(Coroutines[index]) ~= "dead"
	-- If status == "dead" then Lock On activity for this coroutine dies too 
end

-- Coroutine function example using coroutine.yield() to suspend 
function f(t)
	local tNext = t
	local file = io.open(lfs.writedir().."/Logs/Export.log", "w")
	file:write(string.format("t = %f, started\n", tNext))
	tNext = coroutine.yield()
	for i = 1,10 do
		file:write(string.format("t = %f, continued\n", tNext))
		tNext = coroutine.yield()
	end
	file:write(string.format("t = %f, finished\n", tNext))
	file:close()
end

-- Create your coroutines and save them in Coriutines table, e.g.:
CoroutineIndex = CoroutineIndex + 1
Coroutines[CoroutineIndex] = coroutine.create(f) 

-- Use LoCreateCoroutineActivity(index, tStart, tPeriod) to plan your coroutines
-- activity at model times, e.g.:
LoCreateCoroutineActivity(CoroutineIndex, 1.0, 3.0) -- to start at 1.0 second with 3.0 seconds period
-- Coroutine output in the Coroutine.log file:
-- t = 1.000000, started
-- t = 4.000000, continued
-- t = 7.000000, continued
-- t = 10.000000, continued
-- t = 13.000000, continued
-- t = 16.000000, continued
-- t = 19.000000, continued
-- t = 22.000000, continued
-- t = 25.000000, continued
-- t = 28.000000, continued
-- t = 31.000000, continued
-- t = 34.000000, finished
--]]


--SimpleRadio - Remove on server?
local dcsSr=require('lfs');dofile(dcsSr.writedir()..[[Scripts\DCS-SimpleRadioStandalone.lua]])

-- AECIS
-- local dcsAECIS=require('lfs');dofile(dcsAECIS.writedir()..[[Scripts\DCS-AECIS.lua]])
