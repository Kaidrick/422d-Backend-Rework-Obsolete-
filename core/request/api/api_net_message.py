from core.request.api.api_request import RequestApi, RequestApiHandle


class RequestNetMessage(RequestApi):
    def __init__(self, player_id, message):
        super(RequestNetMessage, self).__init__(RequestApiHandle.MESSAGE)
        self.message = message
        self.player_id = player_id


if __name__ == '__main__':
    RequestNetMessage(1, "are you the local player?").send()
