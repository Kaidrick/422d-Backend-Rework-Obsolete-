import sys
import os
import configparser

cfg = configparser.ConfigParser()
cfg_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'config') + "/backend.cfg"
cfg.read(cfg_file_path)

PORT = int(cfg['DEFAULT']['miz_port'])  # The port used by the mission env server
API_PORT = int(cfg['DEFAULT']['api_port'])  # The port used by net API server
DATA_PORT = int(cfg['DEFAULT']['exp_port'])  # The port use by the export data server

TIMEOUT = float(cfg['RECONNECTION']['timeout'])
RETRY = float(cfg['RECONNECTION']['retry'])
INTERVAL = float(cfg['RECONNECTION']['interval'])

HOST = cfg['HOST']['address']  # The server's hostname or IP address
# HOST = '104.128.72.58'

EOT = '␄'  # End of transmission character
CHAR_PER_SECOND = int(cfg['INGAME_MESSAGE']['character_per_second'])
CONST_MSG_COMP = int(cfg['INGAME_MESSAGE']['message_duration_compensate'])

if cfg['DEBUG']['show_request'].lower() == 'true':
    SHOW_REQUEST = True
else:
    SHOW_REQUEST = False


class Map:
    BLACK_SEA = "Caucasus"
    NTTR = "Nevada"
    NORMANDY = "Normandy"
    PERSIAN_GULF = "Persian Gulf"


GAME_MAP = Map.NTTR

PY_EH = sys.version
DEBUG_DEFAULT = "trigger.action.outText('Python " + PY_EH + "', 10)"
