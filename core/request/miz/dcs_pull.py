from core.request.miz.dcs_request import RequestHandle, RequestDcs
from core.request.miz.dcs_radio_menu import response_to_radio_item_pull


class RequestDcsPull(RequestDcs):
    def __init__(self, ):
        super(RequestDcsPull, self).__init__(handle=RequestHandle.PULL)


def process_pulls():
    all_pulls = RequestDcsPull().send()
    if all_pulls:  # not None
        for pull in all_pulls:
            pt = pull['type']
            if pt == 1:  # response to radio item
                response_to_radio_item_pull(pull)
