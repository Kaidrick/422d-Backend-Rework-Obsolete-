from .weapon_data_mapping import weapon_data_process, weapon_shot_logger
from ..precise_data import ExportParseHandler
from ...request.miz.dcs_event import EventHandler

ExportParseHandler.AfterExport["weapon_data_process"] = weapon_data_process
EventHandler.SHOT["weapon_shot_log"] = weapon_shot_logger


