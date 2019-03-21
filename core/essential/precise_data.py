from core.request.exp.export_data import RequestExportUnitsData, RequestExportBallisticData
import core.data_interface as cdi


def extract_export_data():
    res_units = RequestExportUnitsData().send()
    res_ballistic = RequestExportBallisticData().send()

    if res_units:
        cdi.export_units = res_units
        # print(res_units)
    if res_ballistic:
        cdi.export_ballistic = res_ballistic
        # print(res_ballistic)


if __name__ == '__main__':
    extract_export_data()
