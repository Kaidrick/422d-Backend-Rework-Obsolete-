from config.settings import CHAR_PER_SECOND, CONST_MSG_COMP
from core.request.miz.dcs_request import RequestDcs, RequestHandle

import math


class MessageType:
    BROADCAST = "broadcast"
    COALITION = "coalition"
    GROUP = "group"
    MOTD = "motd"
    LOG = "log"


class RequestDcsMessage(RequestDcs):  # default broadcast message and notice
    def __init__(self, content, message_type="log", duration=1, clearview=False):
        super().__init__(handle=RequestHandle.MESSAGE)
        self.content = content
        self.type = message_type
        self.duration = duration
        self.clearview = clearview

        if self.duration == 1:
            self.set_message_duration()

    # @property
    # def content(self):
    #     return self.__content
    #
    # @content.setter
    # def content(self, content):
    #     self.__content = content

    def set_message_duration(self):
        self.duration = get_message_duration(self.content)


class RequestDcsBroadcast(RequestDcsMessage):
    def __init__(self,
                 content,
                 message_type=MessageType.BROADCAST,
                 duration=1):
        super().__init__(content, message_type, duration)


class RequestDcsMOTD(RequestDcsMessage):
    def __init__(self, motd_imp, content, message_type=MessageType.MOTD, duration=1):
        super(RequestDcsMOTD, self).__init__(content, message_type, duration)
        self.motd_imp = motd_imp


class RequestDcsMessageForCoalition(RequestDcsMessage):
    def __init__(self,
                 content=">>>RequestDcsMessageForCoalition",
                 message_type=MessageType.COALITION,
                 duration="1",
                 coalition=2):
        super().__init__(content, message_type, duration)
        self.coalition = coalition


class RequestDcsMessageForGroup(RequestDcsMessage):
    def __init__(self,
                 group_id,
                 content=">>>RequestDcsMessageForCoalition",
                 message_type=MessageType.GROUP,
                 duration=1,
                 clearview=False):
        super().__init__(content, message_type, duration)
        self.clearview = clearview
        self.group_id = group_id
        if self.duration == 1:
            self.set_message_duration()


def get_message_duration(message_content):  # message_content is a string, maybe a list of string?
    if type(message_content) == str:
        length = len(message_content)
        duration = length / CHAR_PER_SECOND + CONST_MSG_COMP
        return math.ceil(duration)
    else:
        raise TypeError('message_content must be a string')
