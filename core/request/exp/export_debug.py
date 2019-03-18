from core.request.exp.export_data import RequestExport, RequestExportHandle


class RequestExportDebug(RequestExport):
    def __init__(self):
        super().__init__(RequestExportHandle.DEBUG)


class RequestExportLuaMemory(RequestExportDebug):
    def __init__(self):
        super().__init__()
        self.type = "mem"


if __name__ == '__main__':
    print(RequestExportLuaMemory().send())
