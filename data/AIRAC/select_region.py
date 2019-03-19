"""This file select all data in the given region"""
regions = {
    'Nevada': {},
    'Caucasus': {},
    'PersianGulf': {},
}


class Region:
    class Nevada:
        boarder = {'north': 0, 'south': 0, 'east': 0, 'west': 0}

    class Caucasus:
        boarder = {'north': 46000000, 'south': 41000000, 'east': 30000000, 'west': 46000000}

    class PersianGulf:
        boarder = {'north': 33000000, 'south': 23000000, 'east': 48000000, 'west': 60000000}


class NavPoint:
    def __init__(self, callsignStr, x, y, id, comment=""):
        self.callsignStr = callsignStr
        self.x = x
        self.y = y
        self.id = id
        self.comment = comment
        self.properties = {
            'vnav': 1,
            'scale': 0,
            'vangle': 0,
            'angle': 0,
            'steer': 2,
        }


if __name__ == '__main__':
    import core.request.miz.dcs_debug as debug
    import time
    import json

    nav_pt_id_cnt = 0
    nav_pts = []
    with open('navaids.txt') as f_obj:
        content = f_obj.readlines()
        print(len(content))
        for navaid in content:
            dt = navaid.rstrip().split("|")
            # print(dt[0], dt[6], dt[7])
            if int(dt[6]) < Region.Caucasus.boarder['north']:
                if int(dt[6]) > Region.Caucasus.boarder['south']:
                    if int(dt[7]) < Region.Caucasus.boarder['west']:
                        if int(dt[7]) > Region.Caucasus.boarder['east']:
                            nav_pt_id_cnt += 1

                            lat = int(dt[6]) / 1000000
                            lon = int(dt[7]) / 1000000
                            # convert to degree

                            coord_lo = debug.RequestDcsDebugCommand(f"return coord.LLtoLO({lat}, {lon})", True).send()
                            nav_pts.append(NavPoint(dt[0], coord_lo['x'], coord_lo['z'], nav_pt_id_cnt, comment=dt[1]).__dict__)
                            print(f"Processed - {dt[0]}: {dt[1]}")
    #                         # time.sleep(0.1)

    with open('waypoints.txt') as f_obj:
        content = f_obj.readlines()
        print(len(content))
        for waypoint in content:
            dt = waypoint.rstrip().split("|")
            # print(dt[0], dt[6], dt[7])
            if int(dt[1]) < Region.Caucasus.boarder['north']:
                if int(dt[1]) > Region.Caucasus.boarder['south']:
                    if int(dt[2]) < Region.Caucasus.boarder['west']:
                        if int(dt[2]) > Region.Caucasus.boarder['east']:
                            nav_pt_id_cnt += 1

                            lat = int(dt[1]) / 1000000
                            lon = int(dt[2]) / 1000000
                            # convert to degree

                            coord_lo = debug.RequestDcsDebugCommand(f"return coord.LLtoLO({lat}, {lon})", True).send()
                            nav_pts.append(NavPoint(dt[0], coord_lo['x'], coord_lo['z'], nav_pt_id_cnt).__dict__)
                            print(f"Processed - {dt[0]}: {dt[1]} {dt[2]}")
                            # time.sleep(0.1)

    # for pt in nav_pts:
    #     print(pt)
    print(f"Total Nav Points: {nav_pt_id_cnt}")
    print(json.dumps(nav_pts))
