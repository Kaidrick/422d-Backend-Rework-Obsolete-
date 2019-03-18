from core.request.api.api_request import RequestApi, RequestApiHandle


# TODO: this file will interact with dcs control api
# when a player perform a specific action, GUI calls back, and python receive a msg from the server
class DcsPlayer:  # create a instance when player connect? add owner unit when a matching name player enters a unit
    def __init__(self, ucid, ipaddr, net_id=-1, name="", airframe="", coalition="", group_id="", language='en', preferred_system='imperial'):
        self.name = name
        self.owner_group_id = group_id
        self.airframe = airframe
        self.coalition = coalition
        self.language = language
        self.preferred_system = preferred_system
        self.ipaddr = ipaddr
        self.ucid = ucid
        self.net_id = net_id
        self.lang_on_ip = False

    def set_lang(self, language):
        self.language = language
        return self

    def set_unit(self, system):
        self.preferred_system = system


class RequestDcsPlayer(RequestApi):
    def __init__(self):
        super().__init__(handle=RequestApiHandle.QUERY)


class RequestPlayerInfo(RequestDcsPlayer):
    def __init__(self):
        super().__init__()
        self.type = "player_info"
        # self.player_name = player_name


class RequestSlotInfo(RequestDcsPlayer):
    def __init__(self):
        super().__init__()
        self.type = "slot_info"


if __name__ == '__main__':
    k = RequestSlotInfo().send()
    print(k)
# get info from dcs server every second
# load data from a file contains ucid key and settings value

# TODO: all connected players will have their ucid mapped to a preference dict. So before doing any interactions (sending message to a player or add radios), always check player settings
# TODO: radio will change ucid-preference dict, while this file is modifiying the dict. Conflict?