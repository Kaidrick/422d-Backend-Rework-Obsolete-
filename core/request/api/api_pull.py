from core.request.api.api_request import RequestApiHandle, RequestApi


class PullType:
    SLOT_CHANGE = "slot_changes"
    CHAT_COMMAND = "chat_cmd"


class RequestApiPull(RequestApi):
    def __init__(self):
        super().__init__(handle=RequestApiHandle.PULL)


class PullSlotChanges(RequestApiPull):
    def __init__(self):
        super().__init__()
        self.type = PullType.SLOT_CHANGE


class PullChatCommand(RequestApiPull):
    def __init__(self):
        super().__init__()
        self.type = PullType.CHAT_COMMAND


class ApiPullHandler:
    SLOT_CHANGE = {}
    CHAT_COMMAND = {}


def on_pull_slot_changes(pull_data):
    for handler_id, handler_method in ApiPullHandler.SLOT_CHANGE.items():
        handler_method(pull_data)


def on_pull_chat_command(pull_data):
    for handler_id, handler_method in ApiPullHandler.CHAT_COMMAND.items():
        handler_method(pull_data)


def process_api_pulls():
    api_pulls = RequestApiPull().send()
    if not api_pulls:
        # print("api pull error", __file__)
        return

    for api_pull in api_pulls:
        print("debug_info", "api_pulls", api_pulls)
        if api_pull['type'] == PullType.SLOT_CHANGE:
            on_pull_slot_changes(api_pull)

        elif api_pull['type'] == PullType.CHAT_COMMAND:
            on_pull_chat_command(api_pull)  # maybe should define chat command in python, init data to lua
