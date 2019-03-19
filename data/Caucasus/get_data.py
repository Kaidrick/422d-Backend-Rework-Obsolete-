import json
from core.request.miz.dcs_debug import RequestDcsDebugCommand

if __name__ == '__main__':
    cleaned_data = {}
    with open('nav_pts.json') as f_obj:
        paste = json.load(f_obj)
        for nav_pt in paste:
            name = nav_pt['callsignStr']
            x = nav_pt['x']
            y = nav_pt['y']

            cleaned_data[name] = {'x': x, 'y': y}

    with open('raw_nav_pts.json', 'w') as f_obj:
        json.dump(cleaned_data, f_obj)
