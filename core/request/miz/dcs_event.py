from core.request.miz.dcs_request import RequestDcs, RequestHandle
import threading

"""
Event [function: request event from server and analyze,
then send a request to respond to the event

example: a player enters an aircraft -> server add this event to a pending table
-> client request event -> client receive this event -> client analyze this event
-> client make a decision -> client send this decision as a request to the server

===? Analyze event:
    what kind of event it is?
        -> what id
        -> is it important?
        
    
    what to do?

    lets deal with S_EVENT_BIRTH and S_EVENT_PLAYER_LEAVE_UNIT first?

"""


class EVENT:
    S_EVENT_INVALID = 0
    S_EVENT_SHOT = 1
    S_EVENT_HIT = 2
    S_EVENT_TAKEOFF = 3
    S_EVENT_LAND = 4
    S_EVENT_CRASH = 5
    S_EVENT_EJECTION = 6
    S_EVENT_REFUELING = 7
    S_EVENT_DEAD = 8
    S_EVENT_PILOT_DEAD = 9
    S_EVENT_BASE_CAPTURED = 10
    S_EVENT_MISSION_START = 11
    S_EVENT_MISSION_END = 12
    S_EVENT_TOOK_CONTROL = 13
    S_EVENT_REFUELING_STOP = 14
    S_EVENT_BIRTH = 15
    S_EVENT_HUMAN_FAILURE = 16
    S_EVENT_ENGINE_STARTUP = 17
    S_EVENT_ENGINE_SHUTDOWN = 18
    S_EVENT_PLAYER_ENTER_UNIT = 19
    S_EVENT_PLAYER_LEAVE_UNIT = 20
    S_EVENT_PLAYER_COMMENT = 21
    S_EVENT_SHOOTING_START = 22
    S_EVENT_SHOOTING_END = 23
    S_EVENT_MARK_ADDED = 24
    S_EVENT_MARK_CHANGE = 25
    S_EVENT_MARK_REMOVED = 26
    S_EVENT_MAX = 27


class DcsEvent:
    def __init__(self, event_lua_table):
        self.id = event_lua_table.id
        self.time = event_lua_table.time


class EventBirth(DcsEvent):
    def __init__(self, event_lua_table):
        super().__init__(event_lua_table)
        self.initiator = event_lua_table.initiator  # the unit in which player birth


class EventPlayerLeaveUnit(DcsEvent):
    def __init__(self, event_lua_table):
        super().__init__(event_lua_table)
        self.initiator = event_lua_table.initiator  # the unit from which the player left


class RequestDcsEvent(RequestDcs):  # request all events in the collection list
    def __init__(self):
        super().__init__(RequestHandle.EVENT)


class RequestDcsPreciseTimingEvent(RequestDcs):
    def __init__(self):
        super().__init__(RequestHandle.PRECISE_EVENT)


class EventHandler:
    BIRTH = {}
    CRASH = {}
    SHOT = {}
    SHOOTING_START = {}
    SHOOTING_END = {}
    ENGINE_STARTUP = {}  # doesn't really work for multi-player
    ENGINE_SHUTDOWN = {}  # doesn't really work for multi-player
    TAKEOFF = {}
    LAND = {}


# DCS Event Shooting Start
def on_event_shooting_start(event_data):
    for handler_id, handler_method in EventHandler.SHOOTING_START.items():
        handler_method(event_data)


# DCS Event Shooting Stop
def on_event_shooting_end(event_data):
    for handler_id, handler_method in EventHandler.SHOOTING_END.items():
        handler_method(event_data)


# DCS Event Shot
def on_event_shot(event_data):
    for handler_id, handler_method in EventHandler.SHOT.items():
        handler_method(event_data)


# DCS Event Birth
def on_event_birth(event_data):
    for handler_id, handler_method in EventHandler.BIRTH.items():
        threading.Thread(target=handler_method, args=[event_data]).start()


# DCS Event Crash
def on_event_crash(event_data):
    for handler_id, handler_method in EventHandler.CRASH.items():
        handler_method(event_data)


# DCS Event Engine Startup
def on_event_engine_startup(event_data):
    for handler_id, handler_method in EventHandler.ENGINE_STARTUP.items():
        handler_method(event_data)


# DCS Event Engine Shutdown
def on_event_engine_shutdown(event_data):
    for handler_id, handler_method in EventHandler.ENGINE_SHUTDOWN.items():
        handler_method(event_data)


# DCS Event Takeoff
def on_event_takeoff(event_data):
    for handler_id, handler_method in EventHandler.TAKEOFF.items():
        handler_method(event_data)


# DCS Event Land
def on_event_land(event_data):
    for handler_id, handler_method in EventHandler.LAND.items():
        handler_method(event_data)


# DCS Precise Timing Event

def process_miz_events():
    all_miz_events = RequestDcsEvent().send()
    for miz_event in all_miz_events:
        if miz_event['id'] == EVENT.S_EVENT_BIRTH:
            on_event_birth(miz_event)

        elif miz_event['id'] == EVENT.S_EVENT_CRASH:
            on_event_crash(miz_event)

        elif miz_event['id'] == EVENT.S_EVENT_ENGINE_STARTUP:
            on_event_engine_startup(miz_event)

        elif miz_event['id'] == EVENT.S_EVENT_ENGINE_SHUTDOWN:
            on_event_engine_shutdown(miz_event)

        elif miz_event['id'] == EVENT.S_EVENT_TAKEOFF:
            on_event_takeoff(miz_event)
            # print(miz_event)

        elif miz_event['id'] == EVENT.S_EVENT_LAND:
            on_event_land(miz_event)
            # print(miz_event)


def process_miz_precise_timing_events():
    all_precise_timing_events = RequestDcsPreciseTimingEvent().send()
    for miz_precise_timing_event in all_precise_timing_events:
        if \
                miz_precise_timing_event['id'] == EVENT.S_EVENT_SHOT:
            on_event_shot(miz_precise_timing_event)

        elif \
                miz_precise_timing_event['id'] == EVENT.S_EVENT_SHOOTING_START:
            on_event_shooting_start(miz_precise_timing_event)

        elif \
                miz_precise_timing_event['id'] == EVENT.S_EVENT_SHOOTING_END:
            on_event_shooting_end(miz_precise_timing_event)
