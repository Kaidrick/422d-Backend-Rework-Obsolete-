"""
Some design note here:
Every single weapon release in NTTR should be recorded
Player release weapon --> weapon release spark --> weapon object generated
--> weapon data updated --> weapon terminal --> weapon terminal spark --> process weapon data
--> sort batch based on release time
--> report to user after leaving live area and entering transitional area
"""
from core.spark import SparkHandler
from core.request.miz.dcs_event import EventHandler
import core.data_interface as cdi

# so this file implements a collector to gather weapon batch data
weapon_release_data = {}  # all weapon that has been released since mission start
# every time a weapon is release, its data is stored here
# need to call spark
# release data is indexed by player name? since name is unique in a mission


def new_weapon_record(spk_dt):  # it only cares when a weapon is final
    # find this reference in cdi
    unit_id_name = spk_dt['data']['runtime_id']  # get weapon runtime id
    munition_object = spk_dt['data']['self']
    munition_object


def weapon_release_event_ref(event_data):
    print(event_data)


SparkHandler.WEAPON_TERMINAL["new_weapon_record"] = new_weapon_record
EventHandler.SHOT["weapon_release_event_ref"] = weapon_release_event_ref
