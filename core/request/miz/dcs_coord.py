"""
This file implements methods that send requests to query coordinate related info such as coord conversion
"""
from core.request.miz.dcs_request import RequestDcs, RequestHandle


class CoordConvType:
    LLtoLO = "LLtoLO"
    LOtoLL = "LOtoLL"
    LLtoMGRS = "LLtoMGRS"
    MGRStoLL = "MGRStoLL"


class RequestCoordConversion(RequestDcs):
    def __init__(self, conv_fmt):
        super().__init__(handle=RequestHandle.QUERY)
        self.type = "coord_conv"
        self.format = conv_fmt


class RequestLLtoLO(RequestCoordConversion):
    def __init__(self, lat, lon, alt=None):
        super().__init__(CoordConvType.LLtoLO)
        self.params = {
            'lat': lat,
            'lon': lon,
            'alt': alt,
        }


class RequestLOtoLL(RequestCoordConversion):
    def __init__(self, x_axis, z_axis, y_axis):  # x, y, z
        super().__init__(CoordConvType.LOtoLL)
        self.params = {
            'x': x_axis,
            'y': y_axis,
            'z': z_axis,
        }


class RequestLLtoMGRS(RequestCoordConversion):
    def __init__(self, lat, lon):
        super().__init__(CoordConvType.LLtoMGRS)
        self.params = {
            'lat': lat,
            'lon': lon,
        }


class RequestMGRStoLL(RequestCoordConversion):
    def __init__(self, UTMZone, MGRSDigraph, Easting, Northing):
        super().__init__(CoordConvType.MGRStoLL)
        self.params = {
            'UTMZone': UTMZone,
            'MGRSDigraph': MGRSDigraph,
            'Easting': Easting,
            'Northing': Northing,
        }


if __name__ == '__main__':
    p = RequestLLtoLO(36.24123, -114.5342, 1551).send()
    print(p)
    q = RequestLLtoMGRS(36.24123, -114.5342).send()
    print(q)
    r = RequestLOtoLL(-396503.375, 27581.85546875, 1551).send()
    print(r)
    s = RequestMGRStoLL("11S", "QA", 21578, 13524).send()
    print(s)
