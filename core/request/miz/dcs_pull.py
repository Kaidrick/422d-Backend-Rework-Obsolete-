from core.request.miz.dcs_request import RequestHandle, RequestDcs


class RequestDcsPull(RequestDcs):
    def __init__(self, ):
        super(RequestDcsPull, self).__init__(handle=RequestHandle.PULL)

