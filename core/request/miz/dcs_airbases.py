from core.request.miz.dcs_request import RequestDcs, RequestHandle
from core.request.miz.dcs_env import airbase_dict, Side
import gettext

_ = gettext.gettext

nevada = [
    _("Creech AFB"),
    _("Groom Lake AFB"),
    _("McCarran International Airport"),
    _("Nellis AFB"),
    _("Beatty Airport"),
    _("Boulder City Airport"),
    _("Echo Bay"),
    _("Henderson Executive Airport"),
    _("Jean Airport"),
    _("Laughlin Airport"),
    _("Lincoln County"),
    _("Mesquite"),
    _("Mina Airport 3Q0"),
    _("North Las Vegas"),
    _("Pahute Mesa Airstrip"),
    _("Tonopah Airport"),
    _("Tonopah Test Range Airfield"),
]

caucasus = [
    _("Anapa"),
    _("Batumi"),
    _("Beslan"),
    _("Gelendzhik"),
    _("Gudauta"),
    _("Khanskaya"),
    _("Kobuleti"),
    _("Kolkhi"),
    _("Krasnodar"),
    _("Krymsk"),
    _("Kutaisi"),
    _("Lochini"),
    _("MinVody"),
    _("Mozdok"),
    _("Nalchik"),
    _("Novorossiysk"),
    _("Pashkovsky"),
    _("Sochi"),
    _("Soganlug"),
    _("Sukhumi"),
    _("Vaziani"),
]

persian_gulf = [
    _("Abu Musa Island Airport"),
    _("Bandar Abbas Intl"),
    _("Bandar Lengeh"),
    _("Al Dhafra AB"),
    _("Dubai Intl"),
    _("Al Maktoum Intl"),
    _("Fujairah Intl"),
    _("Tunb Island AFB"),
    _("Havadarya"),
    _("Khasab"),
    _("Lar Airbase"),
    _("Al Minhad AB"),
    _("Qeshm Island"),
    _("Sharjah Intl"),
    _("Sirri Island"),
    _("Tunb Kochak"),
    _("Sir Abu Nuayr"),
    _("Kerman Airport"),
    _("Shiraz International Airport"),
    _("Sas Al Nakheel Airport"),
    _("Bandar-e-Jask airfield"),
    _("Abu Dhabi International Airport"),
    _("Al-Bateen Airport"),
    _("Kish International Airport"),
    _("Al Ain International Airport"),
    _("Lavan Island Airport"),
    _("Jiroft Airport"),
]


class AirBaseType:
    AIRPORT = 0
    HELIPAD = 1
    SHIP = 2


# DCS Airbase class
class Airbase:
    def __init__(self, name, pos, coal):  # default neutral
        self.name = name
        self.coalition = coal
        self.pos = pos


class Airport(Airbase):
    def __init__(self, name, pos, coal):
        super().__init__(name, pos, coal)
        self.type = AirBaseType.AIRPORT


class Helipad(Airbase):
    def __init__(self, name, pos, coal):
        super().__init__(name, pos, coal)
        self.type = AirBaseType.HELIPAD


class Ship(Airbase):
    def __init__(self, name, pos, coal):
        super().__init__(name, pos, coal)
        self.type = AirBaseType.SHIP


# DCS Airport Requests
class RequestAirbase(RequestDcs):
    def __init__(self):
        super().__init__(handle=RequestHandle.QUERY)
        self.type = "airport"


class RequestBlueAirbase(RequestAirbase):
    def __init__(self):
        super().__init__()
        self.coalition = Side.BLUE


class RequestRedAirbase(RequestAirbase):
    def __init__(self):
        super().__init__()
        self.coalition = Side.RED


class RequestNeutralAirbase(RequestAirbase):
    def __init__(self):
        super().__init__()
        self.coalition = Side.NEUTRAL


class RequestAllAirbase(RequestAirbase):
    def __init__(self):
        super().__init__()
        self.coalition = -1


def init_airbases():
    airbases = RequestAllAirbase().send()
    for ab in airbases:
        pos = ab['loc']
        name = ab['name']
        coal = ab['coal']
        s_type = ab['type']

        if s_type is AirBaseType.AIRPORT:
            kn_ab = Airport(name, pos, coal)
        elif s_type is AirBaseType.HELIPAD:
            kn_ab = Helipad(name, pos, coal)
        elif s_type is AirBaseType.SHIP:  # TODO: provide ship related information
            kn_ab = Ship(name, pos, coal)

        #print(kn_ab.__dict__)
        airbase_dict[name] = kn_ab


def print_airbases_name_as_code():
    for kn_name in airbase_dict.keys():
        msg = '_("' + kn_name + '"),'
        print(msg)
