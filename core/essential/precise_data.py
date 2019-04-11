from core.request.exp.export_data import RequestExportUnitsData, RequestExportBallisticData, RequestExportOmniData
import core.data_interface as cdi
import time


class ExportParseHandler:
    BeforeExport = {}
    AfterExport = {}


def exec_before_export(export_timestamp):
    for handler_id, handler_method in ExportParseHandler.BeforeExport.items():
        handler_method(export_timestamp)


def exec_after_export(export_timestamp):
    for handler_id, handler_method in ExportParseHandler.AfterExport.items():
        handler_method(export_timestamp)


def extract_export_data():
    res_omni = RequestExportOmniData().send()
    # res_units = RequestExportUnitsData().send()
    # res_ballistic = RequestExportBallisticData().send()

    # TODO: combine export data on lua side? is it possible?
    if res_omni:
        cdi.export_omni = res_omni
        # print(res_omni)

    # if res_units:
    #     cdi.export_units = res_units
        # print(res_units)
    # if res_ballistic:
    #     cdi.export_ballistic = res_ballistic
        # print(res_ballistic)


def export_step():
    export_timestamp = time.time()
    exec_before_export(export_timestamp)
    extract_export_data()  # Export from Export.lua
    exec_after_export(export_timestamp)

    # print("tick", time.time())


if __name__ == '__main__':
    extract_export_data()
