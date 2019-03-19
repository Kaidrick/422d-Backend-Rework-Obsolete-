from core.game_object_control.dcs_set_command import DcsSetCommand, CommandType


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


class ActivateBeacon(DcsSetCommand):
    def __init__(self, group_id, beacon_type, system, callsign,
                 unit_id=None, mode_channel=None,
                 channel=None, a2a=None, bearing=None, delay=0):
        super().__init__(CommandType.ACTIVATE_BEACON, group_id)
        self.params = {
            'type': beacon_type,
            'AA': a2a,
            'unitId': unit_id,
            'modeChannel': mode_channel,
            'channel': channel,
            'system': system,
            'callsign': callsign,
            'bearing': bearing,
            'frequency': 1087000000 + channel * 1000000,
        }
        self.delay = delay


class Start(DcsSetCommand):
    def __init__(self, group_id):
        super().__init__(CommandType.START, group_id)
        self.params = {}


class SetImmortal(DcsSetCommand):
    def __init__(self, group_id, is_immortal=True):
        super().__init__(CommandType.SET_IMMORTAL, group_id)
        self.params = {
            'value': is_immortal
        }


if __name__ == '__main__':
    from core.game_object_control import AI

    kmd = """local sid = Unit.getByName('新飞机群组'):getID()
            trigger.action.outText(sid, 10)
    """
    # RequestDcsDebugCommand(kmd).send()

    ActivateBeacon("新飞机群组", AI.BeaconType.BEACON_TYPE_TACAN,
                   AI.BeaconSystem.TACAN_TANKER, "PTO",
                   mode_channel="X", channel=1, bearing=True).send()

