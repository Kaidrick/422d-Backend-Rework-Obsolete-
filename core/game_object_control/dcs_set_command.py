from core.request.miz.dcs_action import DcsAction, ActionType


class CommandType:
    SET_FREQUENCY = "SetFrequency"
    TRANSMIT_MESSAGE = "TransmitMessage"
    STOP_TRANSMISSION = "StopTransmission"
    ACTIVATE_BEACON = "ActivateBeacon"
    START = "Start"
    EPLRS = "EPLRS"
    SET_CALLSIGN = "SetCallsign"
    STOP_ROUTE = "StopRoute"
    SET_IMMORTAL = "SetImmortal"
    SET_INVISIBLE = "SetInvisible"


class DcsSetCommand(DcsAction):  # command is always set to a group or a unit?
    def __init__(self, cmd_id, group_id, delay=0):  # group id?
        # so lua should know these attributes
        super().__init__(ActionType.CONTROLLER)
        self.control_action = "set_command"
        self.id = cmd_id
        self.group_id = group_id
        self.delay = delay

    def as_task(self):
        return self.__dict__


# TODO: re-structure the code, move to game_object_control
class SetFrequency(DcsSetCommand):
    def __init__(self, group_id, power=10, modulation=0, frequency=121500000, delay=0):  # default frequency is guard, use AM
        super().__init__(CommandType.SET_FREQUENCY, group_id)
        self.params = {
            'power': power,
            'modulation': modulation,  # 0 for AM, 1 for FM?
            'frequency': frequency,
        }
        self.delay = delay


class TransmitMessage(DcsSetCommand):  # this is a request
    def __init__(self, group_id, message, duration, loop=False, file="Notice", delay=0):
        super().__init__(CommandType.TRANSMIT_MESSAGE, group_id)
        self.params = {
            'loop': loop,
            'duration': duration,
            'subtitle': message,
            'file': file,
        }
        self.delay = delay


class StopTransmission(DcsSetCommand):  # this is a request
    def __init__(self, group_id, delay=0):
        super().__init__(CommandType.STOP_TRANSMISSION, group_id)
        self.params = {}
        self.delay = delay


class SetImmortal(DcsSetCommand):
    def __init__(self, group_id, is_immortal=True, delay=0):
        super(SetImmortal, self).__init__(CommandType.SET_IMMORTAL, group_id)
        self.params = {
            'value': is_immortal
        }
        self.delay = delay


class SetInvisible(DcsSetCommand):
    def __init__(self, group_id, is_invisible=True, delay=0):
        super(SetInvisible, self).__init__(CommandType.SET_INVISIBLE, group_id)
        self.params = {
            'value': is_invisible
        }
        self.delay = delay
