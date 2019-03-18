from core.request.miz.dcs_request import RequestDcs, RequestHandle
from config.settings import DEBUG_DEFAULT


class DebugType:
    LUA_STRING = "dostring"
    ENV_INFO = "env"


class RequestDcsDebug(RequestDcs):
    def __init__(self):
        super().__init__(RequestHandle.DEBUG)


class RequestDcsDebugEnvInfo(RequestDcsDebug):  # TODO: Finish RequestDcsDebugEnvInfo
    def __init__(self, parameter):
        super().__init__()
        self.type = DebugType.ENV_INFO
        self.parameter = parameter


class RequestDcsDebugCommand(RequestDcsDebug):
    def __init__(self, lua_string=DEBUG_DEFAULT,
                 echo_result=False,
                 outText=False):
        super().__init__()
        self.type = DebugType.LUA_STRING
        self.content = lua_string
        self.echo_result = echo_result  # server send back dostring result?
        self.outText = outText

    def run_script(self, lua_string):
        self.content = lua_string


# if __name__ == '__main__':
    # import time
    # import core.utility.utils as utils
    # from core.request.exp.export_data import RequestExportUnitsData
    # p = RequestExportUnitsData().send()
    # trk_ids = []
    # for k, v in p.items():
    #     if v['Flags']['RadarActive']:
    #         p_id = k[3:]
    #         trk_ids.append(utils.bake_object_id(p_id))
    #
    # print(trk_ids)
    #
    # while True:
    #     cmd = f"""
    #     local r1, p1 = Unit.getRadar({trk_ids[0]})
    #     --local r2, p2 = Unit.getRadar({trk_ids[1]})
    #     --local r3, p3 = Unit.getRadar({trk_ids[2]})
    #     local radar_tbl = {{
    #                         {{r1, p1}},
    #                         --{{r2, p2}},
    #                         --{{r3, p3}}
    #     }}
    #     return radar_tbl
    #     """
    #     res = RequestDcsDebugCommand(cmd, True).send()
    #     print(res)
    #
    #     time.sleep(3)

if __name__ == '__main__':
    RequestDcsDebugCommand("trigger.action.outText('test', 10)").send()


    # while True:
    #     print(RequestDcsDebugCommand("return collectgarbage('count')", True).send())
    #     time.sleep(1)

    # debug_cmd = """
    #     all_airbases = world.getAirbases()
    #     airbases_data = {}
    #     for _, airbase in pairs(all_airbases) do
    #         local parkings = airbase:getParking()
    #         local ab_id = airbase:getID()
    #         local ab_name = airbase:getName()
    #         local ab_pos = airbase:getPosition().p
    #         airbases_data[tostring(ab_id)] = {
    #             ["id"] = ab_id,
    #             ["name"] = ab_name,
    #             ["pos"] = ab_pos,
    #             ["parking"] = parkings,
    #         }
    #     end
    #     return airbases_data"""
    # k = RequestDcsDebugCommand(debug_cmd, True).send()

    # kcmd = """
    # local ref = coalition.getRefPoints(2)
    # return ref
    # """
    # k = RequestDcsDebugCommand(kcmd, True).send()
    #
    # print(json.dumps(k))

    # kmd = """
    # all_airbases = world.getAirbases()
    # for _, airbase in pairs(all_airbases) do
    #     env.info(airbase:getName() .. mist.utils.tableShow(airbase:getDesc()))
    # end
    # """
    # RequestDcsDebugCommand(kmd).send()
    # import time
    # power = 1
    # x = -284486
    # z = -87279
    # y = 1345
    #
    # for n in range(0, 2):  # 30
    #     power += 1
    #     # y += n
    #     # x += 50
    #     # z += 0
    #     for p in range(-3, 3):
    #         y += 0.5
    #         kmd = f"""
    #             trigger.action.explosion({{x = {x}, z = {z}, y = {y}}}, {power})
    #         """
    #         print(kmd)
    #         RequestDcsDebugCommand(kmd).send()
    #         time.sleep(0.1)

#     kmd = """
# vec3 = coord.LLtoLO(36.78346, -115.445916, 1067)
#
# trigger.action.smoke(vec3, 0)    """
#     RequestDcsDebugCommand(kmd).send()

