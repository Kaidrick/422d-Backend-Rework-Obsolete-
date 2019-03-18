from core.request.api.api_request import RequestApiHandle, RequestApi
from config.settings import DEBUG_DEFAULT


class NetDebugType:
    NET_DOSTRING = "net_dostring"
    NET_ENV = "net_env"
    NET_MEM = "mem"
    NET_API_LOADSTRING = "api_loadstring"


class NetEnvType:
    SERVER = "server"
    MISSION = "mission"  # holds current mission
    EXPORT = "export"   # runs $WRITE_DIR/Scripts/Export.lua and the relevant export API
    CONFIG = "config"   # the state in which $INSTALL_DIR/Config/main.cfg is executed, as well as $WRITE_DIR/Config/autoexec.cfg used for configuration settings


class RequestApiDebug(RequestApi):
    def __init__(self):
        super().__init__(RequestApiHandle.DEBUG)


class RequestApiMemory(RequestApiDebug):
    def __init__(self):
        super().__init__()
        self.type = NetDebugType.NET_MEM


class RequestAPINetDostring(RequestApiDebug):
    def __init__(self, lua_string="", env=NetEnvType.SERVER, echo_result=False):
        super().__init__()
        self.type = NetDebugType.NET_DOSTRING
        self.content = lua_string
        self.echo_result = echo_result
        self.env = env

    def run_script(self, lua_string):
        self.content = lua_string

    def env(self, env):
        self.env = env


class RequestApiLoadString(RequestApiDebug):
    def __init__(self, lua_string="", echo_result=False):
        super().__init__()
        self.type = NetDebugType.NET_API_LOADSTRING
        self.content = lua_string
        self.echo_result = echo_result


if __name__ == '__main__':
    # RequestAPINetDostring(DEBUG_DEFAULT, echo_result=True, env=NetEnvType.SERVER).send()
    p_info = RequestApiLoadString("return net.get_player_info(1)", echo_result=True).send()
    if p_info['slot'] == '':
        print("no in a unit. use chat echo")
    else:
        print(p_info['slot'])
        print(p_info)
        print("use in game message for this unit")


