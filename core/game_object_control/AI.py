class Task:
    class AltitudeType:
        BARO = "BARO"
        RADIO = "RADIO"

    class Designation:
        AUTO = "Auto"
        IR_POINTER = "IR-Pointer"
        LASER = "Laser"
        NO = "No"
        WP = "WP"

    class OrbitPattern:
        CIRCLE = "Circle"
        RACE_TRACK = "Race-Track"

    class TurnMethod:
        FIN_POINT = "Fin Point"
        FLY_OVER_POINT = "Fly Over Point"

    class VehicleFormation:
        CONE = "Cone"
        DIAMOND = "Diamond"
        ECHELON_LEFT = "EchelonL"
        ECHELON_RIGHT = "EchelonR"
        OFF_ROAD = "Off Road"
        ON_ROAD = "On Road"
        RANK = "Rank"
        VEE = "Vee"

    class WaypointType:
        LAND = "Land"
        TAKEOFF = "TakeOff"
        TAKEOFF_PARKING = "TakeOffParking"
        TAKEOFF_PARKING_HOT = "TakeOffParkingHot"

    class WeaponExpend:
        ALL = "All"
        FOUR = "Four"
        HALF = "Half"
        ONE = "One"
        QUARTER = "Quarter"
        TWO = "Two"


class Skill:
    AVERAGE = "Average"
    CLIENT = "Client"
    EXCELLENT = "Excellent"
    GOOD = "Good"
    HIGH = "High"
    PLAYER = "Player"


class Option:
    class Air:
        class id:
            ECM_USING = 13
            FLARE_USING = 4
            FORMATION = 5
            MISSILE_ATTACK = 18
            NO_OPTION = -1
            OPTION_RADIO_USAGE_CONTACT = 21
            OPTION_RADIO_USAGE_ENGAGE = 22
            OPTION_RADIO_USAGE_KILL = 23
            PROHIBIT_AA = 14
            PROHIBIT_AB = 16
            PROHIBIT_AG = 17
            PROHIBIT_JETT = 15
            PROHIBIT_WP_PASS_REPORT = 19
            RADAR_USING = 3
            REACTION_ON_THREAT = 1
            ROE = 0
            RTB_ON_BINGO = 6
            RTB_ON_OUT_OF_AMMO = 10
            SILENCE = 7

        class val:
            class ECM_USING:
                ALWAYS_USE = 3
                NEVER_USE = 0
                USE_IF_DETECTED_LOCK_BY_RADAR = 2
                USE_IF_ONLY_LOCK_BY_RADAR = 1

            class FLARE_USIN:
                AGAINST_FIRED_MISSILE = 1
                NEVER = 0
                WHEN_FLYING_IN_SAM_WEZ = 2
                WHEN_FLYING_NEAR_ENEMIES = 3

            class MISSILE_ATTACK:
                HALF_WAY_RMAX_NEZ = 2
                MAX_RANGE = 0
                NEZ_RANGE = 1
                RANDOM_RANGE = 4
                TARGET_THREAT_EST = 3

            class RADAR_USING:
                FOR_ATTACK_ONLY = 1
                FOR_CONTINUOUS_SEARCH = 3
                FOR_SEARCH_IF_REQUIRED = 2
                NEVER = 0

            class REACTION_ON_THREAT:
                ALLOW_ABORT_MISSION = 4
                BYPASS_AND_ESCAPE = 3
                EVADE_FIRE = 2
                NO_REACTION = 0
                PASSIVE_DEFENCE = 1

            class ROE:
                OPEN_FIRE = 2
                OPEN_FIRE_WEAPON_FREE = 1
                RETURN_FIRE = 3
                WEAPON_FREE = 0
                WEAPON_HOLD = 4

    class Ground:
        class id:
            ALARM_STATE = 9
            DISPERSE_ON_ATTACK = 8
            ENGAGE_AIR_WEAPONS = 20
            FORMATION = 5
            NO_OPTION = -1
            ROE = 0

        class val:
            class ALARM_STATE:
                AUTO = 0
                GREEN = 1
                RED = 2

            class ROE:
                OPEN_FIRE = 2
                RETURN_FIRE = 3
                WEAPON_HOLD = 4

    class Naval:
        class id:
            NO_OPTION = -1
            ROE = 0

        class val:
            class ROE:
                OPEN_FIRE = 2
                RETURN_FIRE = 3
                WEAPON_HOLD = 4


class BeaconType:
    BEACON_TYPE_NULL = 0
    BEACON_TYPE_VOR = 1
    BEACON_TYPE_DME = 2
    BEACON_TYPE_VOR_DME = 3
    BEACON_TYPE_TACAN = 4
    BEACON_TYPE_VORTAC = 5
    BEACON_TYPE_RSBN = 32
    BEACON_TYPE_BROADCAST_STATION = 1024
    BEACON_TYPE_HOMER = 8
    BEACON_TYPE_AIRPORT_HOMER = 4104
    BEACON_TYPE_AIRPORT_HOMER_WITH_MARKER = 4136
    BEACON_TYPE_ILS_FAR_HOMER = 16408
    BEACON_TYPE_ILS_NEAR_HOMER = 16456
    BEACON_TYPE_ILS_LOCALIZER = 16640
    BEACON_TYPE_ILS_GLIDESLOPE = 16896
    BEACON_TYPE_NAUTICAL_HOMER = 32776


class BeaconSystem:
    PAR_10 = 1
    RSBN_5 = 2
    TACAN = 3
    TACAN_TANKER = 4
    ILS_LOCALIZER = 5
    ILS_GLIDESLOPE = 6
    BROADCAST_STATION = 7

