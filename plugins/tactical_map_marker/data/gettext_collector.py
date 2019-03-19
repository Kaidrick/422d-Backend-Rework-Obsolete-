"""This file iterates through all json data in a folder and write all entry to a single pot file"""
import polib
import json
import os

# theatre = 'Nevada'
# theatre = 'PersianGulf'
# theatre = 'Caucasus'


def load_data(theatre):
    search_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), theatre)
    res = {}
    for filename in os.listdir(search_path):
        if filename.endswith('.json'):
            with open(os.path.join(search_path, filename)) as f:
                _dict = json.load(f)
                res[filename[:-5]] = _dict

    return res


if __name__ == '__main__':
    marker_data = load_data('Nevada')
    po = polib.POFile()

    msgids = []

    for block_area, area_data in marker_data.items():
        for marker_entry in area_data:  # use name, desc and entry
            if 'landmark' == marker_entry['type']:  # ignore, entry field, because it's empty
                for key, value in marker_entry.items():  # get name and desc
                    if key not in ['type', 'pos', 'pack', 'entry'] and value not in msgids:
                        # print(value)
                        po_entry = polib.POEntry(
                            msgid=value,
                            msgstr="",
                        )
                        po.append(po_entry)
                        msgids.append(value)
            else:  # entry field is not empty
                for key, value in marker_entry.items():  # get name and desc
                    if key not in ['type', 'pos', 'pack'] and value not in msgids:
                        # print(value)
                        po_entry = polib.POEntry(
                            msgid=value,
                            msgstr="",
                        )
                        po.append(po_entry)
                        msgids.append(value)

    for data in po:
        print(data)

    po.save('marker_data.pot')
